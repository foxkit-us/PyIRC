#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from logging import getLogger
from base64 import b64encode, b64decode

from PyIRC.extension import BaseExtension, hook, PRIORITY_FIRST
from PyIRC.event import EventState
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


class SASLBase(BaseExtension):

    """ Base SASL support. Does nothing on its own. """

    # We should come after things like STARTTLS
    priority = PRIORITY_FIRST + 5
    requires = ["CapNegotiate"]

    method = None

    def __init__(self, base, **kwargs):

        self.base = base

        self.mechanisms = set()
        self.username = kwargs.get("sasl_username")
        self.password = kwargs.get("sasl_password")

        self.done = False
        self.authenticated = False

    @property
    def caps(self):
        cap_negotiate = self.get_extension("CapNegotiate")

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
        self.done = False

    @hook("commands_cap", "ack")
    def auth(self, event):
        cap_negotiate = self.get_extension("CapNegotiate")

        if self.done:
            # Finished authentication
            return
        elif self.method == None:
            raise NotImplementedError("Need an authentication method!")
        elif "sasl" not in cap_negotiate.remote:
            # CAP nonexistent
            return

        if cap_negotiate.remote["sasl"]:
            # 3.2 style
            self.mechanisms = set(c.lower() for c in
                                  cap_negotiate.remote["sasl"])

        self.send("AUTHENTICATE", [self.method])

        # Defer end of CAP
        event.status = EventState.cancel

    @hook("commands", Numerics.RPL_SASLSUCCESS)
    def success(self, event):
        logger.info("SASL authentication succeeded as %s", self.username)

        self.done = True
        self.authenticated = True
        self.get_extension("CapNegotiate").cont(event)

    @hook("commands", Numerics.ERR_SASLFAIL)
    @hook("commands", Numerics.ERR_SASLTOOLONG)
    @hook("commands", Numerics.ERR_SASLABORTED)
    def fail(self, event):
        logger.info("SASL authentication failed as %s", self.username)

        self.done = True
        self.get_extension("CapNegotiate").cont(event)

    @hook("commands", Numerics.ERR_SASLALREADY)
    def already(self, event):
        logger.critical("Tried to log in twice, this shouldn't happen!")

    @hook("commands", Numerics.RPL_SASLMECHS)
    def get_mechanisms(self, event):
        self.mechanisms = set(event.line.params[1].lower().split(','))
        logger.info("Supported SASL mechanisms: %r", self.mechanisms)


class SASLPlain(SASLBase):

    # Least preferred auth method
    priority = PRIORITY_FIRST + 10

    method = "PLAIN"

    def __init__(self, base, **kwargs):
        super().__init__(base, **kwargs)

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
        for l in (sendstr[i:i+400] for i in range(0, len(sendstr), 400)):
            self.send("AUTHENTICATE", [l])

        event.status = EventState.cancel
