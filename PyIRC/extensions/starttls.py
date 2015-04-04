#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


from functools import partial
from logging import getLogger

from base import BaseExtension, PRIORITY_FIRST, EVENT_CANCEL
from extensions.cap import EVENT_CAP_LS, EVENT_CAP_ACK
from numerics import Numerics


logger = getLogger(__name__)


class STARTTLS(BaseExtension):
    """ Support STARTTLS """

    priority = PRIORITY_FIRST
    requires = ["CapNegotiate"]
    
    def __init__(self, base, **kwargs):

        self.base = base

        self.implements = {
            Numerics.RPL_STARTTLS : self.wrap,
            Numerics.ERR_STARTTLS : self.abort,
        }

        self.hooks = {
            EVENT_CAP_LS : self.register_starttls,
            EVENT_CAP_ACK : self.starttls,
        }

        self.done = False

    def register_starttls(self):
        if self.base.ssl:
            # Unnecessary
            return

        cap_negotiate = self.get_extension("CapNegotiate")

        if "tls" not in cap_negotiate.remote:
            return
        else:
            logger.debug("Beginning STARTTLS negotiation")
            cap_negotiate.register("tls")

    def starttls(self):
        if self.base.ssl:
            # Unnecessary
            return

        cap_negotiate = self.get_extension("CapNegotiate")

        if "tls" in cap_negotiate.local and not self.done:
            self.send("STARTTLS", None)

            return EVENT_CANCEL

    def wrap(self, line):
        logger.info("Performing STARTTLS initiation...")
        self.base.wrap_ssl()
        
        self.done = True
        cap_negotiate = self.get_extension("CapNegotiate")
        cap_negotiate.cont()

    def abort(self):
        logger.critical("STARTTLS initiation failed, connection not secure")
        self.base.socket = self.base._socket
        del self.base._socket

        self.done = True
        cap_negotiate = self.get_extension("CapNegotiate")
        cap_negotiate.cont()

