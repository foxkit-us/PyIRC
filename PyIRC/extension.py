# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


from logging import getLogger
from PyIRC.numerics import Numerics
from PyIRC.event import HookEvent, LineEvent


PRIORITY_DONTCARE = 0
PRIORITY_FIRST = -1000
PRIORITY_LAST = 1000


logger = getLogger(__name__)


class BaseExtension:
    """ The base class for extensions.

    Members:
    - commands - the set of IRC commands and numerics this extension
      supports
    - hooks - hooks this command supports
    - requires - required extensions (must be a name)
    - priority - the priority of this extension, lower is higher (like Unix)
    """

    priority = PRIORITY_DONTCARE
    commands = {}
    hooks = {}
    requires = []

    def __init__(self, base, **kwargs):
        self.base = base

    def send(self, command, params):
        """ Mirror self.base.send """

        self.base.send(command, params)

    def schedule(self, time, callback):
        """ Mirror self.base.schedule """

        return self.base.schedule(time, callback)

    def unschedule(self, sched):
        """ Mirror self.base.unschedule """

        self.base.unschedule(sched)

    def get_extension(self, extension):
        """ Mirror self.base.get_extension """

        return self.base.get_extension(extension)

    def call_event(self, cls, event, *args):
        """ Mirror self.base.call_event """

        return self.base.call_event(cls, event, *args)

    def casefold(self, string):
        """ Mirror self.base.casefold """

        return self.base.casefold(string)


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
