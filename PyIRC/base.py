#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Library base classes

Contains the most fundamental parts of PyIRC. This is the glue that binds
everything together.
"""


from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from itertools import zip_longest
from logging import getLogger

from PyIRC.numerics import Numerics
from PyIRC.casemapping import IRCString
from PyIRC.line import Line
from PyIRC.extension import ExtensionManager
from PyIRC.hook import hook, build_hook_table
from PyIRC.event import EventManager, EventState


logger = getLogger(__name__)


class IRCBase(metaclass=ABCMeta):

    """The base IRC class meant to be used as a base for more concrete
    implementations.

    :ivar events:
        Our :py:class:`~PyIRC.event.EventManager` instance.

    :ivar extensions:
        Our :py:class:`~PyIRC.extension.ExtensionManager` instance.

    :ivar connected:
        If True, we have connected to the server successfully.

    :ivar registered:
        If True, we have completed the server handshake and are ready
        to send commands.
    """

    priority = 10000

    def __init__(self, serverport, username, nick, gecos, extensions,
                 **kwargs):
        """Initialise the IRC base.

        :param serverport:
            (server, port) sequence, similar to the form passed to
            socket.connect.

        :param username:
            The username to send to the server.
            .. note:: identd may override this.

        :param nick:
            The nickname to use.

        :param extensions:
            Sequence of default extensions to use.

        Keyword arguments (extensions may use others):

        :key ssl:
            Whether or not to use SSL. Set to an :py:class:`ssl.SSLContext``
            to specify custom parameters, or ``True`` for defaults.

        :key server_password:
            Server password (PASS).

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
        events = self.events = EventManager()

        # Basic IRC state
        self.connected = False
        self.registered = False
        self.case = IRCString.RFC1459

        # Extension manager system
        if not extensions:
            raise ValueError("Need at least one extension")
        self.extensions = ExtensionManager(self, kwargs, events, extensions)
        self.extensions.create_db()

        # Create hooks
        build_hook_table(self)
        events.register_callbacks_from_inst_all(self)

    def case_change(self):
        """Change server casemapping semantics

        Do not call this unless you know what you're doing
        """
        if not hasattr(self, "isupport"):
            case = "RFC1459"
        else:
            case = self.isupport.get("CASEMAPPING").upper()

        if case == "ASCII":
            case = IRCString.ASCII
        elif case == "RFC1459":
            case = IRCString.RFC1459
        else:
            case = IRCString.UNICODE

        if case == self.case:
            return

        self.case = case
        self.events.call_event("hooks", "case_change")

    def casefold(self, string):
        """Fold a nick according to server case folding rules.

        :param string:
            The string to casefold according to the IRC server semantics.
        """
        return IRCString(self.case, string).casefold()

    def casecmp(self, string, other):
        """Do a caseless comparison of two strings.

        Returns True if equal, or False if not.

        :param string:
            String to compare
        :param other:
            String to compare
        """
        return self.casefold(string) == self.casefold(other)

    def get_extension(self, extension):
        """A convenience method for
        :py:meth:`~PyIRC.extension.ExtensionManager.get_extension`"""
        return self.extensions.get_extension(extension)

    def call_event(self, hclass, event, *args, **kwargs):
        """A convenience method for
        :py:meth:`~PyIRC.event.EventManager.call_event`"""
        return self.events.call_event(hclass, event, *args, **kwargs)
    
    def call_event_inst(self, hclass, event, inst):
        """A convenience method for
        :py:meth:`~PyIRC.event.EventManager.call_event_inst`"""
        return self.events.call_event_inst(hclass, event, inst)

    def connect(self):
        """Do the connection handshake """
        # XXX late binding sucks but we can't do it in __init__.
        # Else we get a chicken and egg problem.
        self.events.register_callbacks_from_inst_all(self)

        return self.events.call_event("hooks", "connected")

    def close(self):
        """Do the connection teardown """
        # XXX cheesy hack
        self.events.unregister_callbacks_from_inst_all(self)

        return self.events.call_event("hooks", "disconnected")

    def recv(self, line):
        """Receive a line.

        :param line:
            A :class:`~PyIRC.line.Line` instance to recieve from the wire.
        """
        command = line.command.lower()

        self.events.call_event("commands", command, line)

    @abstractmethod
    def send(self, command, params):
        """Send a line out onto the wire.

        :param command:
            IRC command to send.

        :param params:
            A Sequence of parameters to send with the command. Only the last
            parameter may contain spaces due to IRC framing format
            limitations.
        """
        line = Line(command=command, params=params)
        event = self.events.call_event("commands_out", command, line)
        if event and event.status == EventState.cancelled:
            return None

        return line

    @abstractmethod
    def schedule(self, time, callback):
        """Schedule a callback for a specific time.

        Returns an object that can be passed to unschedule. The object should
        be treated as opaque.

        :param float time:
            Seconds into the future to perform the callback.
        :param callback:
            Callback to perform. Use :meth:`functools.partial` to pass arguments.
        """
        raise NotImplementedError()

    @abstractmethod
    def unschedule(self, sched):
        """Unschedule a callback previously registered with schedule.

        :param sched:
            Event to unschedule returned by schedule.
        """
        raise NotImplementedError()

    def wrap_ssl(self):
        """Wrap the underlying connection with an SSL connection.

        .. warning::
            Not all backends support this!
        """
        raise NotImplementedError()
