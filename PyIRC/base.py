#!/usr/bin/env python3
# Copyright © 2015 A. Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Library base classes.

Contains the most fundamental parts of PyIRC. This is the glue that
binds everything together.

"""


from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from logging import getLogger

from PyIRC.signal import SignalStorage
from PyIRC.casemapping import IRCString
from PyIRC.line import Line
from PyIRC.extensions import get_extension


_logger = getLogger(__name__)  # pylint: disable=invalid-name


class Event:
    """A basic event passed around extensions, wherein state can be set.

    :ivar cancelled:
        The present event is "soft cancelled". Other events may undo this.
    """
    def __init__(self, eventname, caller, cancelled=False):
        self.eventname = eventname
        self.caller = caller
        self.cancelled = cancelled


class IRCBase(metaclass=ABCMeta):

    """The base IRC class meant to be used as a base for more concrete
    implementations.

    :ivar connected:
        If True, we have connected to the server successfully.

    :ivar registered:
        If True, we have completed the server handshake and are ready
        to send commands.

    """

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

        :key bindport:
            (address, port) to bind to.

        .. note::
            Keyword arguments may be used by extensions. kwargs is passed
            as-is to all extensions.

        """
        super().__init__()

        self.server, self.port = serverport
        self.username = username
        self.nick = nick
        self.gecos = gecos
        self.ssl = kwargs.get("ssl", False)
        self.server_password = kwargs.get("server_password")
        self.bindport = kwargs.get("bindport")

        self.kwargs = kwargs

        # Basic IRC state
        self.connected = False
        self.registered = False
        self.case = IRCString.RFC1459

        self.signals = SignalStorage()

        # Extension manager system
        if not extensions:
            raise ValueError("Need at least one extension")

        self.extensions = OrderedDict()
        for extension in extensions:
            self.load_extension(extension)

        # Do the signal storage binding for us now
        self.signals.bind(self)

    def load_extension(self, extension):
        """Load a single extension.

        :param extension:
            The extension to load, either a string, or a
            :py:class:`~PyIRC.extensions.BaseExtension` instance. If extension
            is a string, the extension is looked up in the list of presently
            known extensions, favouring built-in PyIRC functions by default.
        """
        if isinstance(extension, str):
            # Get the extension from a string
            extname = extension
            extension = get_extension(extension)
            if extension is None:
                raise ValueError("Extension not found: {}".format(extname))
        else:
            extname = extension.__name__

        if extname in self.extensions:
            return

        requires = getattr(extension, "requires", ())
        for require in requires:
            self.load_extension(require)

        extension = self.extensions[extname] = extension(base=self,
                                                         **self.kwargs)
        self.signals.bind(extension)

    def unload_extension(self, extension):
        """Unload an extension.

        :param extension:
            The extension to unload, either a string, or a
            :py:class:`~PyIRC.extension.BaseExtension` instance.

        .. warning::
            Reverse dependencies are not yet checked! Be careful when
            unloading extensions. Also, since state is not saved in the
            default modules, this should never be reused for reloading.

        """
        if isinstance(extension, str):
            extname = extension
        else:
            extname = extension.__name__

        extension = self.extensions.pop(extname, None)
        if extname is None:
            raise ValueError("Extension not found: {}".format(extname))

        self.signals.unbind(extension)

    def get_extension_subclasses(self, base_extension):
        """Find all subclasses of the given extension.

        For the given extension class, return all subclasses of that extension
        that are actually loaded right now.

        Extensions will be returned in order of loading.

        :param base_extension:
            Extension base class to search for subclasses for.

        :returns:
            A list of tuples containing the extension names and instances, in
            order of loading.

        """
        extensions = []
        for name, extension in self.extensions.items():
            if isinstance(extension, base_extension):
                extensions.append((name, extension))

        return extensions

    def case_change(self):
        """Change server casemapping semantics.

        Do not call this unless you know what you're doing

        """
        if not hasattr(self, "isupport"):
            case = "RFC1459"
        else:
            isupport = self.isupport  # pylint: disable=no-member
            case = isupport.get("CASEMAPPING").upper()

        if case == "ASCII":
            case = IRCString.ASCII
        elif case == "RFC1459":
            case = IRCString.RFC1459
        else:
            case = IRCString.UNICODE

        if case == self.case:
            return

        self.case = case
        self.call_event("protocol", "case_change")

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
        """Get the instance of a given extension.

        :returns:
            The extension requested.

        """
        return self.extensions[extension]

    def call_event(self, hclass, event, *args, **kwargs):
        """Call an (hclass, event) signal.

        If no args are passed in, and the signal is in a deferred state, the
        arguments from the last call_event will be used.

        :returns:
            An (:py:class:`~PyIRC.base.Event`, return values from events)
            tuple.

        .. warning::
            This does not preserve the Event instance for deferred calls.

        """

        signal_name = (hclass, event)
        signal = self.signals.get_signal(signal_name)
        event = Event(signal_name, self)

        if not signal.slots:
            return (event, [])

        return (event, signal.call(event, *args, **kwargs))

    def resume_event(self, hclass, event):
        """Resume a deferred event.

        This is a small wrapper around
        :py:meth:`~PyIRC.base.IRCBase.call_event`, but checks that the signal
        is deferred.

        :returns:
            An (:py:class:`~PyIRC.base.Event`, return values from events)
            tuple, if the event is deferred; else it returns None.

        """
        signal = self.signals.get_signal((hclass, event))

        if signal.last_status != signal.STATUS_DEFER:
            return

        return self.call_event(hclass, event)

    def connect(self):
        """Do the connection handshake."""
        return self.call_event("link", "connected")

    def close(self):
        """Do the connection teardown."""
        return self.call_event("link", "disconnected")

    def recv(self, line):
        """Receive a line.

        :param line:
            A :class:`~PyIRC.line.Line` instance to recieve from the wire.

        """
        command = line.command

        self.call_event("commands", command, line)

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
        event, results = self.call_event("commands_out", command, line)
        if event.cancelled:
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
            Callback to perform. Use :meth:`functools.partial` to pass
            arguments.

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
