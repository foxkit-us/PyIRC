#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


""" Library base classes

Contains the most fundamental parts of PyIRC. This is the glue that binds
everything together.
"""


from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from logging import getLogger

from PyIRC.numerics import Numerics
from PyIRC.casemapping import IRCString
from PyIRC.line import Line
from PyIRC.extension import ExtensionManager
from PyIRC.hook import HookGenerator, hook
from PyIRC.event import EventManager


logger = getLogger(__name__)


class ABCMetaHookGenerator(HookGenerator, ABCMeta):
    """ A stub metaclass for IRCBase """


class IRCBase(metaclass=ABCMetaHookGenerator):

    """ The base IRC class meant to be used as a base for more concrete
    implementations.

    The following attributes are available:

    events
        Our event.EventManager instance

    extensions
        Our event.ExtensionManager instance

    connected
        If True, we have connected to the server successfully.

    registered
        If True, we have completed the server handshake and are ready to send
        commands.
    """

    priority = 10000

    def __init__(self, serverport, username, nick, gecos, extensions,
                 **kwargs):
        """ Initialise the IRC base.

        Arguments:

        serverport
            (server, port) sequence, similar to the form passed to
            socket.connect

        username
            the username to send to the server (identd may override this)

        nick
            The nickname to use

        extensions
            Sequence of default extensions to use

        Keyword arguments (extensions may use others):

        ssl
            whether or not to use SSL

        server_password
            server password

        .. note::

            Keyword arguments may be used by extensions. kwargs is passed
            as-is to all extensions.
        """

        self.server, self.port = serverport
        self.username = username
        self.nick = nick
        self.gecos = gecos
        self.ssl = kwargs.get("ssl", False)
        self.server_password = kwargs.get("server_password")

        self.kwargs = kwargs

        # Event state
        self.events = EventManager()

        # Extension manager system
        assert extensions
        self.extensions = ExtensionManager(self, kwargs, self.events,
                                           extensions)
        self.extensions.create_db()

        # Create hooks
        for hclass, reg in self.events.events_reg.items():
            self.events.register_callbacks_from_inst(hclass, self)

        # Basic IRC state
        self.connected = False
        self.registered = False

    def casefold(self, string):
        """ Fold a nick according to server case folding rules

        Arguments:

        string
            string to casefold according to the IRC server semantics.
        """

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
        """ Receive a line

        Arguments:

        line
            a Line instance to recieve from the wire. It is expected that it
            has already been parsed.
        """

        command = line.command.lower()

        self.events.call_event("commands", command, line)

    @abstractmethod
    def send(self, command, params):
        """ Send a line out onto the wire

        Arguments:

        command
            IRC command to send

        params
            A Sequence of parameters to send with the command. Only the last
            parameter may contain spaces due to IRC framing format
            limitations.
        """

        return Line(command=command, params=params)

    @abstractmethod
    def schedule(self, time, callback):
        """ Schedule a callback for a specific time

        Returns an object that can be passed to unschedule. The object should
        be treated as opaque.

        Arguments:

        time
            Seconds into the future to perform the callback
        callback
            Callback to perform. Use functools.partial to pass other arguments.
        """

        raise NotImplementedError()

    @abstractmethod
    def unschedule(self, sched):
        """ Unschedule a callback previously registered with schedule

        Arguments:

        sched
            Event to unschedule returned by schedule
        """

        raise NotImplementedError()

    def wrap_ssl(self):
        """ Wrap the underlying connection with an SSL connection

        Not all backends support this!
        """

        raise NotImplementedError()
