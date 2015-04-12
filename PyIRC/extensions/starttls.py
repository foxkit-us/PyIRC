#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Automatic SSL negotiation

It's a little like the ESMTP STARTTLS command, but the server does not forget
all of the client state after it is issued. Therefore, it should be issued as
quickly as possible.
"""


from logging import getLogger

from PyIRC.extension import BaseExtension
from PyIRC.hook import hook, PRIORITY_FIRST
from PyIRC.event import EventState
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


class StartTLS(BaseExtension):

    """ Support for the STARTTLS extension.

    Not all I/O backends support this, notably io.asyncio.
    """

    requires = ["CapNegotiate"]

    def __init__(self, base, **kwargs):
        self.base = base

        self.done = False

        if not self.base.ssl:
            self.caps = {
                "tls" : [],
            }

    @hook("hooks", "disconnected")
    def close(self, event):
        self.done = False 

    @hook("cap_perform", "ack", PRIORITY_FIRST)
    def starttls(self, event):
        if self.base.ssl:
            # Unnecessary
            return

        if self.done:
            return

        if "tls" in event.caps:
            self.done = True
            self.send("STARTTLS", None)
            event.status = EventState.cancel

    @hook("commands", Numerics.RPL_STARTTLS)
    def wrap(self, event):
        logger.info("Performing STARTTLS initiation...")
        self.base.wrap_ssl()

        cap_negotiate = self.get_extension("CapNegotiate")
        cap_negotiate.cont()

    @hook("commands", Numerics.ERR_STARTTLS)
    def abort(self, event):
        logger.critical("STARTTLS initiation failed, connection not secure")

        cap_negotiate = self.get_extension("CapNegotiate")
        cap_negotiate.cont()
