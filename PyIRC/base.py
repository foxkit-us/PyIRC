#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.

from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from logging import getLogger

from PyIRC.numerics import Numerics
from PyIRC.casemapping import IRCString
from PyIRC.line import Line
from PyIRC.extension import ExtensionManager
from PyIRC.event import EventManager, HookEvent, LineEvent


logger = getLogger(__name__)


class IRCBase(metaclass=ABCMeta):

    """ The base IRC class meant to be used as a base for more concrete
    implementations. """

    def __init__(self, serverport, username, nick, gecos, extensions,
                 **kwargs):
        """ Initialise the IRC base.

        Arguments:
        - serverport - server/port combination, like passed to socket.connect
        - username - username to send to the server (identd may override this)
        - nick - nickname to use
        - extensions - list of default extensions to use (BasicRFC recommended)

        Keyword arguments:
        - ssl - whether or not to use SSL
        - other extensions may provide their own
        """

        self.server, self.port = serverport
        self.username = username
        self.nick = nick
        self.gecos = gecos
        self.ssl = kwargs.get("ssl", False)

        self.kwargs = kwargs

        # Event state
        self.events = EventManager()

        # Extensions
        self.extensions = ExtensionManager(self, kwargs, self.events,
                                           extensions)
        self.extensions.create_db()

        # Basic IRC state
        self.connected = False
        self.registered = False

    def casefold(self, string):
        """ Fold a nick according to server case folding rules """

        isupport = self.extensions.get_extension("ISupport")
        casefold = isupport.supported.get("CASEMAPPING", "RFC1459")

        if casefold == "ASCII":
            return IRCString.ascii_casefold(string)
        elif casefold == "RFC1459":
            return IRCString.rfc1459_casefold(string)
        else:
            return string.casefold()

    def connect(self):
        """ Do the connection handshake """

        self.events.call_event("hooks", "connected")

    def close(self):
        """ Do the connection teardown """

        self.events.call_event("hooks", "disconnected")

    def recv(self, line):
        """ Receive a line """

        command = line.command.lower()

        self.events.call_event("commands", command, line)

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
