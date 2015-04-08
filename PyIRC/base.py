#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.

from abc import ABCMeta, abstractmethod
from collections import defaultdict, OrderedDict
from operator import itemgetter
from logging import getLogger

from PyIRC.numerics import Numerics
from PyIRC.line import Line
from PyIRC.event import EventManager, HookEvent, LineEvent


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
            self.base.send("USER", [self.base.user, "*", "*",
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


class IRCBase(metaclass=ABCMeta):

    """ The base IRC class meant to be used as a base for more concrete
    implementations. """

    def __init__(self, serverport, user, nick, gecos, extensions, **kwargs):
        """ Initialise the IRC base.

        Arguments:
        - serverport - server/port combination, like passed to socket.connect
        - user - username to send to the server (identd may override this)
        - nick - nickname to use
        - extensions - list of default extensions to use (BasicRFC recommended)

        Keyword arguments:
        - ssl - whether or not to use SSL
        - other extensions may provide their own
        """

        self.server, self.port = serverport
        self.user = user
        self.nick = nick
        self.gecos = gecos
        self.ssl = kwargs.get("ssl", False)

        self.extensions = list(extensions)

        self.kwargs = kwargs

        # Event state
        self.events = EventManager()

        # Basic state
        self.connected = False
        self.registered = False

        self.extensions_db = OrderedDict()

        self.build_extensions_db()

    def get_extension(self, extension):
        """ Get a given extension from the db """

        return self.extensions_db.get(extension, None)

    def build_extensions_db(self):
        """ Enumerate the extensions list, creating instances """

        self.extensions_db.clear()
        self.events.clear()

        # Commands
        self.events.register_class("commands", LineEvent)

        # Hooks
        self.events.register_class("hooks", HookEvent)

        # Some default hooks
        self.events.register_event("hooks", "connected")
        self.events.register_event("hooks", "disconnected")
        self.events.register_event("hooks", "extension_post")

        requires = set()

        for e in self.extensions:
            extinst = e(self, **self.kwargs)
            self.extensions_db[e.__name__] = extinst

            requires.update(extinst.requires)

            logger.info("Loading extension: %s", e.__name__)

        # Ensure all requires are met
        for req in requires:
            if req not in self.extensions_db:
                raise KeyError("Required extension not found: {}".format(req))

        self.build_call_cache()

    def build_hooks(self, cls, attr, key=None):
        """ Register hooks from extensions with the given member for hooks """

        items = self.extensions_db.items()
        for order, (name, extinst) in enumerate(items):
            priority = extinst.priority

            exttable = getattr(extinst, attr, None)
            if exttable is None:
                continue

            logger.info("Loading hook %s for %s", attr, name)

            for hook, callback in exttable.items():
                if key:
                    hook = key(hook)

                self.events.register_callback(cls, hook, priority, callback)

                logger.debug("Hook callback (%s) added: %s", cls, hook)

    def build_call_cache(self):
        """ Enumerate present extensions and build the commands and hooks
        cache.

        You should only need to call this method if you modify the extensions
        list.
        """

        commands_key = lambda s : (s.lower() if isinstance(s, str) else
                                   s.value)
        self.build_hooks("commands", "commands", commands_key)
        self.build_hooks("hooks", "hooks")

        # Post-load hook
        self.call_event("hooks", "extension_post")

    def call_event(self, event, *args):
        """ Dispatch a given event """

        return self.events.call_event(event, *args)

    def connect(self):
        """ Do the connection handshake """

        self.call_event("hooks", "connected")

    def close(self):
        """ Do the connection teardown """

        self.call_event("hooks", "disconnected")

    def recv(self, line):
        """ Receive a line """

        command = line.command.lower()

        self.call_event("commands", command, line)

    @abstractmethod
    def send(self, command, params):
        """ Send a line """

        return Line(command=command, params=params)

    @abstractmethod
    def schedule(self, time, callback):
        """ Schedule a callback for a specific time """

        raise NotImplementedError()

    @abstractmethod
    def unschedule(self, sched):
        """ Unschedule a callback previously registered with schedule """

        raise NotImplementedError()

    def wrap_ssl(self):
        """ Wrap the socket in SSL """

        raise NotImplementedError()
