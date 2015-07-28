#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Identification to services.

SASL is a mechanism used by IRCv3 to authenticate clients to services in a
standard and user-friendly way. A variety of mechanisms are supported by most
servers, but only PLAIN is supported by this module at the moment.

"""


from logging import getLogger
from base64 import b64encode

from taillight.signal import SignalDefer

from PyIRC.signal import event
from PyIRC.extensions import BaseExtension
from PyIRC.numerics import Numerics


_logger = getLogger(__name__)  # pylint: disable=invalid-name


class SASL(BaseExtension):

    """The framework for SASL support. Authentication providers are needed to
    actually provide the authentication.

    :ivar mechanisms_server:
        Mechanisms supported by the server

    :ivar mechanisms:
        Mechanisms we support as a list, which is initalised at connect time.

    :ivar authenticated:
        Whether or not we are authenticated to services

    """

    requires = ["CapNegotiate"]

    method = None
    """ Authentication method to use """

    def __init__(self, *args, **kwargs):
        """Initalise the SASL extension.

        :key sasl_mechanisms:
            An iterable of authentication providers to use, as classes. By
            default, PLAIN and EXTERNAL are used.

        """
        super().__init__(*args, **kwargs)

        self.mechanisms_server = set()

        self.username = kwargs.get("sasl_username")
        self.password = kwargs.get("sasl_password", None)

        self.authenticated = False

        self.providers = kwargs.get("sasl_mechanisms",
                                    [SASLPlain, SASLExternal])
        self.mechanisms = []
        self.attempt = 0

    def _create_mechanisms(self):
        """Initialise the mechanisms list."""
        self.attempt = 0
        self.mechanisms = []
        for mech in self.providers:
            provider = mech(self)
            if provider.can_authenticate:
                self.mechanisms.append(provider)

        if not self.mechanisms:
            _logger.critical("No SASL auth methods are usable!")

    @property
    def caps(self):
        """Return the SASL cap negotiation.

        :returns:
            Either "sasl" or a list of mechanisms, depending on what CAP version
            the server is using.
        """

        if not self.mechanisms:
            self._create_mechanisms()

        if not self.mechanisms:
            return None

        cap_negotiate = self.base.cap_negotiate

        if "sasl" not in cap_negotiate.remote:
            # No SASL
            return None
        elif not cap_negotiate.remote["sasl"]:
            # 3.1 style SASL
            _logger.debug("Registering old-style SASL capability")
            return {"sasl" : []}
        else:
            # 3.2 style SASL
            _logger.debug("Registering new-style SASL capability")
            return {"sasl": [m.method for m in self.mechanisms]}

    @event("link", "disconnected")
    def close(self, _):
        """Clean up all our state since we are disconnected now."""
        self.authenticated = False

        self.mechanisms_server.clear()
        self.mechanisms = []
        self.attempt = 0

    @event("cap_perform", "ack", priority=100)
    def auth(self, _, line, caps):
        """Initiate authentication to the server."""
        # Lower priority to ensure STARTTLS comes before
        if "sasl" not in caps or not self.mechanisms:
            return

        cap_negotiate = self.base.cap_negotiate
        if cap_negotiate.remote["sasl"]:
            # 3.2 style
            params = cap_negotiate.remote["sasl"]
            self.mechanisms_server = set(c.lower() for c in params)

            # Filter out methods we can't use
            self.mechanisms = [m for m in self.mechanisms if m.method in
                               params]
            if not self.mechanisms:
                _logger.critical("Server does not support any of our "
                                 "authentication mechanisms!")
                return

        # Choose a method
        self.send("AUTHENTICATE", [self.mechanisms[0].method])

        # Defer end of CAP
        raise SignalDefer()

    @event("commands", Numerics.RPL_SASLSUCCESS)
    def success(self, _, line):
        """Set up state and resume the CAP event; we're authenticated!"""
        # pylint: disable=unused-argument
        _logger.info("SASL auth succeeded as %s", self.username)

        self.authenticated = True

        if self.base.services_login:
            # No need to authenticate
            self.base.services_login.authenticated = True

        self.mechanisms = []
        self.attempt = 0

        # Resume CAP processing
        return self.resume_event("cap_perform", "ack")

    @event("commands", Numerics.ERR_SASLFAIL)
    @event("commands", Numerics.ERR_SASLABORTED)
    def fail(self, _, line):
        """Try to use the next mechanism since this one failed, or give up."""
        # pylint: disable=unused-argument
        _logger.warning("SASL auth method %s failed as %s",
                        self.mechanisms[self.attempt].method, self.username)

        if self.attempt + 1 >= len(self.mechanisms):
            _logger.critical("No SASL auth methods were successful.")
            return self.resume_event("cap_perform", "ack")
        else:
            # We will try another mechanism
            self.attempt += 1
            mechanism = self.mechanisms[self.attempt]
            self.send("AUTHENTICATE", [mechanism.method])

    @event("commands", Numerics.ERR_SASLTOOLONG)
    def fail_hard(self, _, line):
        """This is called if SASL has a hard failure (possibly due to a bug in
        the library)."""
        _logger.warning("SASL auth method %s hard failed with numeric %s",
                        self.mechanisms[self.attempt].method, line.command)

    @event("commands", Numerics.ERR_SASLALREADY)
    def already(self, _, line):
        # pylint: disable=unused-argument
        _logger.critical("Tried to log in twice, this shouldn't happen!")

        # Err on the side of caution...
        return self.resume_event("cap_perform", "ack")

    @event("commands", Numerics.RPL_SASLMECHS)
    def get_mechanisms(self, _, line):
        """Retrieve the SASL mechanisms supported by the server."""
        self.mechanisms_server = set(line.params[1].lower().split(','))
        _logger.info("Supported SASL mechanisms: %r", self.mechanisms_server)

    @event("commands", "AUTHENTICATE")
    def authenticate(self, _, line):
        """Try to authenticate with the server."""
        if self.attempt >= len(self.mechanisms):
            _logger.critical("Server requested to authenticate when we "
                             "exhausted auth methods!")
            self.send("AUTHENTICATE", ["+"])
            return

        sendstr = self.mechanisms[self.attempt].authenticate(line)
        for t in (sendstr[i:i + 400] for i in range(0, len(sendstr), 400)):
            # 400 is the max limit
            self.send("AUTHENTICATE", [t])

        if len(sendstr) % 400 == 0:
            self.send("AUTHENTICATE", ["+"])


class SASLAuthProviderBase:

    """Base SASL authentication provider."""

    method = None
    """Authentication method to attempt to use."""

    def __init__(self, extension):
        self.extension = extension
        self.base = extension.base

    @property
    def can_authenticate(self):
        """Return whether or not we can authenticate."""
        raise NotImplementedError

    def authenticate(self, line):
        """Return the string to send via AUTHENTICATE."""
        raise NotImplementedError


class SASLExternal(SASLAuthProviderBase):

    """EXTERNAL authentication, usually CERTFP.

    .. warning::
        This is not recommended on servers that use SHA-1 as their certificate
        hashing mechanism (almost all), as SHA-1 is considered weak, and it is
        possible an adversary could collide your certificate in theory.

    """

    method = "EXTERNAL"

    @property
    def can_authenticate(self):
        """Whether or not we can authenticate with this method."""
        return self.base.ssl and self.extension.password is None

    def authenticate(self, line):
        """Implement the EXTERNAL (certfp) authentication method."""
        _logger.info("Logging in with EXTERNAL method as %s",
                     self.extension.username)

        if line.params[-1] != '+':
            return

        # Generate the string for sending
        sendstr = "{0}\0{0}\0".format(self.extension.username)
        sendstr = b64encode(sendstr.encode("utf-8", "replace"))

        # b64encode returns bytes, but our parser expects a str *sigh*
        sendstr = sendstr.decode("utf-8")

        return sendstr


class SASLPlain(SASLAuthProviderBase):

    """PLAIN authentication.

    No security or encryption is performed on the string sent to the
    server, but still suitable for use over TLS.

    """

    method = "PLAIN"

    @property
    def can_authenticate(self):
        """Whether or not we can authenticate with this method."""
        return self.extension.username and self.extension.password

    def authenticate(self, line):
        """Implement the plaintext authentication method."""
        _logger.info("Logging in with PLAIN method as %s",
                     self.extension.username)

        if line.params[-1] != '+':
            return

        # Generate the string for sending
        sendstr = "{0}\0{0}\0{1}".format(self.extension.username,
                                         self.extension.password)
        sendstr = b64encode(sendstr.encode("utf-8", "replace"))

        # b64encode returns bytes, but our parser expects a str *sigh*
        sendstr = sendstr.decode("utf-8")

        return sendstr
