#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


from logging import getLogger

from PyIRC.base import BaseExtension, PRIORITY_FIRST
from PyIRC.event import EventState
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


class STARTTLS(BaseExtension):
    """ Support STARTTLS """

    priority = PRIORITY_FIRST
    requires = ["CapNegotiate"]
    
    def __init__(self, base, **kwargs):

        self.base = base

        self.commands = {
            Numerics.RPL_STARTTLS : self.wrap,
            Numerics.ERR_STARTTLS : self.abort,
        }

        self.hooks = {
            "disconnected" : self.close,
        }

        self.commands_cap = {
            "reg_support" : self.register_starttls,
            "ack" : self.starttls,
        }

        self.done = False

    def register_starttls(self, event):
        if self.base.ssl:
            # Unnecessary
            return

        cap_negotiate = self.get_extension("CapNegotiate")

        if "tls" not in cap_negotiate.remote:
            return
        else:
            logger.debug("Beginning STARTTLS negotiation")
            cap_negotiate.register("tls")

    def starttls(self, event):
        if self.base.ssl:
            # Unnecessary
            return

        cap_negotiate = self.get_extension("CapNegotiate")

        if "tls" in cap_negotiate.local and not self.done:
            self.send("STARTTLS", None)

            event.status = EventState.cancel

    def close(self, event):
        self.done = False

    def wrap(self, event):
        logger.info("Performing STARTTLS initiation...")
        self.base.wrap_ssl()
        
        self.done = True
        cap_negotiate = self.get_extension("CapNegotiate")
        cap_negotiate.cont(event)

    def abort(self, event):
        logger.critical("STARTTLS initiation failed, connection not secure")
        self.base.socket = self.base._socket
        del self.base._socket

        self.done = True
        cap_negotiate = self.get_extension("CapNegotiate")
        cap_negotiate.cont(event)

