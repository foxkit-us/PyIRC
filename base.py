#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.

from abc import ABCMeta, abstractmethod
from collections import defaultdict, OrderedDict
from operator import itemgetter
from logging import getLogger

from numerics import Numerics
from line import Line


PRIORITY_DONTCARE = 0
PRIORITY_FIRST = -1
PRIORITY_LAST = 1


EVENT_OK = None  # default
EVENT_CANCEL = 1  # End processing
EVENT_TERMINATE_SOON = 2  # Disconnect
EVENT_TERMINATE_NOW = 3  # Quit


EVENT_CONNECTED = 1  # Connected to server
EVENT_DISCONNECTED = 2  # Disconnected


logger = getLogger(__name__)


class BaseExtension:

    priority = PRIORITY_DONTCARE
    implements = {}
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

    def dispatch_event(self, table, event, *args):
        """ Mirror self.base.dispatch_event """

        return self.base.dispatch_event(table, event, *args)


class BasicRFC(BaseExtension):
    """ Basic RFC1459 doodads """

    priority = PRIORITY_LAST

    def __init__(self, base, **kwargs):
        self.base = base

        self.implements = {
            "NOTICE" : self.connected,
            "PING" : self.pong,
            Numerics.RPL_WELCOME : self.welcome,
        }

        self.hooks = {
            EVENT_CONNECTED : self.handshake,
            EVENT_DISCONNECTED : self.disconnected,
        }

    def connected(self, line):
        self.base.connected = True

    def handshake(self):
        if not self.base.registered:
            self.base.send("USER", [self.base.user, "*", "*",
                                    self.base.gecos])
            self.base.send("NICK", [self.base.nick])

    def disconnected(self):
        self.base.connected = False

    def pong(self, line):
        self.base.send("PONG", line.params)

    def welcome(self, line):
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
        
        # Basic state
        self.connected = False
        self.registered = False

        self.hooks = defaultdict(list)
        self.dispatch = defaultdict(list)
        self.extensions_db = OrderedDict()

        self.build_extensions_db()

    def get_extension(self, extension):
        """ Get a given extension from the db """

        return self.extensions_db.get(extension, None)

    def build_extensions_db(self):
        """ Enumerate the extensions list, creating instances """

        self.extensions_db.clear()

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

        self.build_dispatch_cache()

    def build_dispatch_cache(self):
        """ Enumerate present extensions and build the dispatch cache.
        
        You should only need to call this method if you modify the extensions
        list.
        """

        self.hooks.clear()
        self.dispatch.clear()

        items = self.extensions_db.items()
        for order, (name, extinst) in enumerate(items):
            logger.info("Loading hooks for: %s", name)

            priority = extinst.priority

            for command, callback in extinst.implements.items():
                if isinstance(command, Numerics):
                    command = command.value

                command = command.lower()

                self.dispatch[command].append([priority, order, callback])
                self.dispatch[command].sort()
                
                logger.debug("Command callback added: %s", command)

            for hook, callback in extinst.hooks.items():
                self.hooks[hook].append([priority, order, callback])
                self.hooks[hook].sort()

                logger.debug("Hook callback added: %s", command)
            
            logger.info("Loaded extension: %s", name)

    def dispatch_event(self, table, event, *args):
        """ Dispatch a given event from the given table """

        for _, _, function in table[event]:
            ret = function(*args)
            if ret == EVENT_CANCEL:
                return EVENT_CANCEL
            elif ret == EVENT_TERMINATE_SOON:
                self.send("QUIT", ["Hook requested termination"])
                return EVENT_TERMINATE_SOON
            elif ret == EVENT_TERMINATE_NOW:
                # XXX should we just raise?
                quit()

    def connect(self):
        """ Do the connection handshake """
        
        self.dispatch_event(self.hooks, EVENT_CONNECTED)

    def close(self):
        """ Do the connection teardown """

        self.dispatch_event(self.hooks, EVENT_DISCONNECTED)

    def recv(self, line):
        """ Receive a line """

        command = line.command.lower()

        self.dispatch_event(self.dispatch, command, line)

    @abstractmethod
    def send(self, command, params):
        """ Send a line """

        return Line(command=command, params=params)

    @abstractmethod
    def schedule(self, time, callback):
        raise NotImplementedError()

    @abstractmethod
    def unschedule(self, sched):
        raise NotImplementedError()
