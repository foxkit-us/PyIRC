#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from logging import getLogger

from PyIRC.extension import BaseExtension, PRIORITY_FIRST
from PyIRC.event import EventState
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


class STARTTLS(BaseExtension):

    """ Support STARTTLS extension. Not all I/O backends support this."""

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
            "ack" : self.starttls,
        }

        self.done = False

        if not self.base.ssl:
            self.caps = {
                "tls" : [],
            }

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

