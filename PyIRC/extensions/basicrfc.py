# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from logging import getLogger

from PyIRC.numerics import Numerics
from PyIRC.extension import BaseExtension, PRIORITY_LAST


logger = getLogger(__name__)


class BasicRFC(BaseExtension):
    """ Basic RFC1459 doodads """

    priority = PRIORITY_LAST

    def __init__(self, base, **kwargs):
        self.base = base

        self.commands = {
            "NOTICE" : self.connected,
            "PING" : self.pong,
            "NICK" : self.nick,
            Numerics.RPL_HELLO : self.connected, # IRCNet
            Numerics.RPL_WELCOME : self.welcome,
        }

        self.hooks = {
            "connected" : self.handshake,
            "disconnected" : self.disconnected,
        }

        self.prev_nick = None

    def connected(self, event):
        self.base.connected = True

    def handshake(self, event):
        if not self.base.registered:
            self.base.send("USER", [self.base.username, "*", "*",
                                    self.base.gecos])
            self.base.send("NICK", [self.base.nick])

    def disconnected(self, event):
        self.base.connected = False
        self.base.registered = False

    def pong(self, event):
        self.base.send("PONG", event.line.params)

    def nick(self, event):
        if event.line.hostmask.nick != self.base.nick:
            return

        # Set nick
        self.prev_nick = self.nick
        self.nick = event.line.params[0]

    def welcome(self, event):
        self.base.registered = True
