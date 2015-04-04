#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


from functools import partial
from logging import getLogger
from base64 import b64encode, b64decode

from PyIRC.base import (BaseExtension, PRIORITY_FIRST, PRIORITY_LAST,
                        EVENT_CANCEL)
from PyIRC.numerics import Numerics

from PyIRC.extensions.cap import EVENT_CAP_LS, EVENT_CAP_ACK

logger = getLogger(__name__)


class SASLBase(BaseExtension):

    """ Base SASL support """

    # We should come after things like STARTTLS
    priority = PRIORITY_FIRST + 5
    requires = ["CapNegotiate"]
    method = None

    def __init__(self, base, **kwargs):

        self.base = base

        self.implements = {
            Numerics.RPL_SASLSUCCESS : self.success,
            Numerics.RPL_SASLMECHS : self.get_mechanisms,
            Numerics.ERR_SASLFAIL : self.fail,
            Numerics.ERR_SASLTOOLONG : self.fail,
            Numerics.ERR_SASLABORTED : self.fail,
            Numerics.ERR_SASLALREADY : self.already,
        }

        self.hooks = {
            EVENT_CAP_LS : self.register_sasl,
            EVENT_CAP_ACK : self.auth,
        }

        self.mechanisms = set()
        self.username = kwargs.get("sasl_username")
        self.password = kwargs.get("sasl_password")

        self.done = False

    def register_sasl(self):
        cap_negotiate = self.get_extension("CapNegotiate")

        if "sasl" not in cap_negotiate.remote:
            # No SASL
            return
        elif len(cap_negotiate.remote["sasl"]):
            # 3.1 style SASL
            logger.debug("Registering old-style SASL capability")
            cap_negotiate.register("sasl")
        else:
            # 3.2 style SASL
            logger.debug("Registering new-style SASL capability")
            cap_negotiate.register("sasl", ["PLAIN"])

    def auth(self):
        cap_negotiate = self.get_extension("CapNegotiate")

        if self.method == None:
            raise NotImplementedError("Need an authentication method!")
        elif "sasl" not in cap_negotiate.local:
            # CAP nonexistent
            return
        elif self.done:
            # Finished authentication
            return

        self.send("AUTHENTICATE", [self.method])

        # Defer end of CAP
        return EVENT_CANCEL

    def success(self, line):
        logger.info("SASL authentication succeeded as %s", self.username)

        self.done = True
        self.get_extension("CapNegotiate").cont()

    def fail(self, line):
        logger.info("SASL authentication failed as %s", self.username)

        self.done = True
        self.get_extension("CapNegotiate").cont()
    
    def already(self, line):
        logger.critical("Tried to log in twice, this shouldn't happen!")

    def get_mechanisms(self, line):
        self.mechanisms = set(line.params[1].lower().split(','))
        logger.info("Supported SASL mechanisms: %r", self.mechanisms)


class SASLPlain(SASLBase):

    # Least preferred auth method
    priority = PRIORITY_FIRST + 10
    method = "PLAIN"

    def __init__(self, base, **kwargs):
        super().__init__(base, **kwargs)

        self.implements.update({
            "AUTHENTICATE" : self.authenticate,
        })

    def authenticate(self, line):
        """ Implement the plaintext authentication method """
    
        logger.info("Logging in with PLAIN method as %s", self.username)

        if line.params[-1] != '+':
            return

        # Generate the string for sending
        sendstr = "{0}\0{0}\0{1}".format(self.username, self.password)
        sendstr = b64encode(sendstr.encode("utf-8", "replace"))

        # b64encode returns bytes, but our parser expects a str *sigh*
        sendstr = sendstr.decode("utf-8")

        # Split into 400-sized chunks
        for l in (sendstr[i:i+400] for i in range(0, len(sendstr), 400)):
            self.send("AUTHENTICATE", [l])

        return EVENT_CANCEL
