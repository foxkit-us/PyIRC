# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Bare minimum IRC RFC standards support."""


from logging import getLogger

from taillight.signal import Signal

from PyIRC.numerics import Numerics
from PyIRC.extension import BaseExtension


_logger = getLogger(__name__)


class BasicRFC(BaseExtension):

    """Basic RFC1459 support.

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base.basic_rfc = self

        self.prev_nick = None
        self.nick = self.base.nick
        self.registered = False

    @Signal(("hooks", "connected")).add_wraps()
    def handshake(self, caller):
        if not self.registered:
            if self.server_password:
                self.send("PASS", [self.server_password])

            self.send("NICK", [self.nick])
            self.send("USER", [self.username, "*", "*",
                               self.gecos])

    @Signal(("hooks", "disconnected")).add_wraps()
    def disconnected(self, caller):
        self.connected = False
        self.registered = False

    @Signal(("commands", Numerics.RPL_HELLO)).add_wraps()
    @Signal(("commands", "NOTICE")).add_wraps()
    def connected(self, caller, line):
        self.connected = True

    @Signal(("commands", "PING")).add_wraps()
    def pong(self, caller, line):
        self.send("PONG", line.params)

    @Signal(("commands", "NICK")).add_wraps()
    def nick(self, caller, line):
        if line.hostmask.nick != self.nick:
            return

        # Set nick
        self.prev_nick = self.nick
        self.nick = line.params[0]

    @Signal(("commands", Numerics.RPL_WELCOME)).add_wraps()
    def welcome(self, caller, line):
        self.registered = True
