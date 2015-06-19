# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


""" Bare minimum IRC RFC standards support """


from logging import getLogger

from PyIRC.numerics import Numerics
from PyIRC.extension import BaseExtension
from PyIRC.hook import hook, PRIORITY_LAST


logger = getLogger(__name__)


class BasicRFC(BaseExtension):

    """ Basic RFC1459 support.

    This is basically just a module that ensures your bot doesn't time out and
    can track its own nick. Nobody is making you use this implementation, but
    it is highly recommended.

    This extension adds ``base.basic_rfc`` as itself as an alias for
    ``get_extension("BasicRFC").``.

    :ivar nick:
        Our present real nickname as reported by the IRC server.

    :ivar prev_nick:
        If we get a NICK event from the server, and it's for us, our last nick
        will be stored here. Useful in case of services collisions that change
        our nick, SANICK/FORCENICK operator abuse, or another extension
        changes our nick.
    """
    priority = PRIORITY_LAST

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base.basic_rfc = self

        self.prev_nick = None
        self.nick = self.base.nick

    @hook("hooks", "connected")
    def handshake(self, event):
        if not self.registered:
            if self.server_password:
                self.send("PASS", [self.server_password])

            self.send("USER", [self.username, "*", "*",
                                    self.gecos])
            self.send("NICK", [self.nick])

    @hook("hooks", "disconnected")
    def disconnected(self, event):
        self.connected = False
        self.registered = False

    @hook("commands", Numerics.RPL_HELLO)
    @hook("commands", "NOTICE")
    def connected(self, event):
        self.connected = True

    @hook("commands", "PING")
    def pong(self, event):
        self.send("PONG", event.line.params)

    @hook("commands", "NICK")
    def nick(self, event):
        if event.line.hostmask.nick != self.nick:
            return

        # Set nick
        self.prev_nick = self.nick
        self.nick = event.line.params[0]

    @hook("commands", Numerics.RPL_WELCOME)
    def welcome(self, event):
        self.registered = True
