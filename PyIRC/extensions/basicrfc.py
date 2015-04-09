# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from logging import getLogger

from PyIRC.numerics import Numerics
from PyIRC.extension import BaseExtension, hook, PRIORITY_LAST


logger = getLogger(__name__)


class BasicRFC(BaseExtension):
    """ Basic RFC1459 doodads """

    priority = PRIORITY_LAST

    def __init__(self, base, **kwargs):
        self.base = base

        self.prev_nick = None
    
    @hook("hooks", "connected")
    def handshake(self, event):
        if not self.base.registered:
            self.base.send("USER", [self.base.username, "*", "*",
                                    self.base.gecos])
            self.base.send("NICK", [self.base.nick])

    @hook("hooks", "disconnected")
    def disconnected(self, event):
        self.base.connected = False
        self.base.registered = False


    @hook("commands", Numerics.RPL_HELLO)
    @hook("commands", "NOTICE")
    def connected(self, event):
        self.base.connected = True

    @hook("commands", "PING")
    def pong(self, event):
        self.base.send("PONG", event.line.params)

    @hook("commands", "NICK")
    def nick(self, event):
        if event.line.hostmask.nick != self.base.nick:
            return

        # Set nick
        self.prev_nick = self.nick
        self.nick = event.line.params[0]

    @hook("commands", Numerics.RPL_WELCOME)
    def welcome(self, event):
        self.base.registered = True
