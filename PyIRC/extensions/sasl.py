#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Identification to services

SASL is a mechanism used by IRCv3 to authenticate clients to services in a
standard and user-friendly way. A variety of mechanisms are supported by most
servers, but only PLAIN is supported by this module at the moment.
"""


from logging import getLogger
from base64 import b64encode, b64decode

from PyIRC.extension import BaseExtension
from PyIRC.hook import hook, PRIORITY_FIRST
from PyIRC.event import EventState
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


class SASLBase(BaseExtension):

    """ Base SASL support. Does nothing on its own.

    :ivar mechanisms:
        Mechanisms supported by the server

    :ivar authenticated:
        Whether or not we are authenticated to services
    """

    # We should come after things like STARTTLS
    priority = PRIORITY_FIRST + 5
    requires = ["CapNegotiate"]

    method = None
    """ Authentication method to use """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mechanisms = set()
        self.username = kwargs.get("sasl_username")
        self.password = kwargs.get("sasl_password")

        self.cap_event = None
        self.authenticated = False

    @property
    def caps(self):
        cap_negotiate = self.base.cap_negotiate

        if "sasl" not in cap_negotiate.remote:
            # No SASL
            return None
        elif not cap_negotiate.remote["sasl"]:
            # 3.1 style SASL
            logger.debug("Registering old-style SASL capability")
            return {"sasl" : []}
        else:
            # 3.2 style SASL
            logger.debug("Registering new-style SASL capability")
            return {"sasl" : [m.method for m in SASLBase.__subclasses__()]}

    @hook("hooks", "disconnected")
    def close(self, event):
        self.mechanisms.clear()
        self.cap_event = None

    @hook("cap_perform", "ack")
    def auth(self, event):
        if self.cap_event or "sasl" not in event.caps:
            return
        elif self.method is None:
            raise NotImplementedError("Need an authentication method!")

        self.authenticated = False

        cap_negotiate = self.base.cap_negotiate
        if cap_negotiate.remote["sasl"]:
            # 3.2 style
            params = cap_negotiate.remote["sasl"]
            self.mechanisms = set(c.lower() for c in params)

        self.send("AUTHENTICATE", [self.method])

        # Defer end of CAP
        self.cap_event = event
        event.status = EventState.pause

    @hook("commands_cap", "end")
    def end_cap(self, event):
        # A quick n' dirty hack used to rearm cap_event
        self.cap_event = None

    @hook("commands", Numerics.RPL_SASLSUCCESS)
    def success(self, event):
        logger.info("SASL authentication succeeded as %s", self.username)

        self.authenticated = True

        services_login = self.base.services_login
        if services_login:
            # No need to authenticate
            services_login.authenticated = True

        cap_negotiate = self.base.cap_negotiate
        cap_negotiate.cont(self.cap_event)

    @hook("commands", Numerics.ERR_SASLFAIL)
    @hook("commands", Numerics.ERR_SASLTOOLONG)
    @hook("commands", Numerics.ERR_SASLABORTED)
    def fail(self, event):
        logger.info("SASL authentication failed as %s", self.username)

        cap_negotiate = self.base.cap_negotiate
        cap_negotiate.cont(self.cap_event)

    @hook("commands", Numerics.ERR_SASLALREADY)
    def already(self, event):
        logger.critical("Tried to log in twice, this shouldn't happen!")

        if self.cap_event and self.cap_event.pause_state:
            # Paused, keep going
            self.fail(event)

    @hook("commands", Numerics.RPL_SASLMECHS)
    def get_mechanisms(self, event):
        self.mechanisms = set(event.line.params[1].lower().split(','))
        logger.info("Supported SASL mechanisms: %r", self.mechanisms)


class SASLPlain(SASLBase):

    """ PLAIN authentication. No security or encryption is performed on the
    string sent to the server, but still suitable for use over TLS. """

    # Least preferred auth method
    priority = PRIORITY_FIRST + 10

    method = "PLAIN"

    @hook("commands", "AUTHENTICATE")
    def authenticate(self, event):
        """ Implement the plaintext authentication method """

        logger.info("Logging in with PLAIN method as %s", self.username)

        if event.line.params[-1] != '+':
            return

        # Generate the string for sending
        sendstr = "{0}\0{0}\0{1}".format(self.username, self.password)
        sendstr = b64encode(sendstr.encode("utf-8", "replace"))

        # b64encode returns bytes, but our parser expects a str *sigh*
        sendstr = sendstr.decode("utf-8")

        # Split into 400-sized chunks
        for l in (sendstr[i:i + 400] for i in range(0, len(sendstr), 400)):
            self.send("AUTHENTICATE", [l])

        # Stop other auth methods.
        event.status = EventState.cancel
