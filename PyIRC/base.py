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
from PyIRC.hook import HookGenerator, hook
from PyIRC.event import EventManager, EventState


logger = getLogger(__name__)


class ABCMetaHookGenerator(HookGenerator, ABCMeta):
    # A stub metaclass for IRCBase
    pass


class IRCBase(metaclass=ABCMetaHookGenerator):

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
            Whether or not to use SSL. Set to an ``SSLContext`` from the ssl
            module to specify custom parameters, or ``True`` for defaults.

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
        events.register_callbacks_from_inst_all(self)

    def case_change(self):
        """Change server casemapping semantics

        Do not call this unless you know what you're doing
        """
        isupport = self.extensions.get_extension("ISupport")
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

    def call_event(self, hclass, event, *args):
        """A convenience method for
        :py:meth:`~PyIRC.event.EventManager.call_event`"""
        return self.events.call_event(hclass, event, *args)
    
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

    def message(self, target, message, notice=False):
        """Send a message to a target.

        :param target:
            Where to send the message, This may be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance,
            :py:class:`~PyIRC.extensions.usertrack.User` instance, or a
            string.

        :param message:
            Message to send

        :param notice:
            Send the message as a notice

        .. warning::
            Use notice judiciously, as many users find them irritating!
        """
        if hasattr(target, "name"):
            # channel
            target = target.name
        elif hasattr(target, "nick"):
            # user
            target = target.nick

        self.send("NOTICE" if notice else "PRIVMSG", [target, message])

    def topic(self, channel, topic):
        """Set the topic in a channel.

        .. note::
            You usually must be opped to set the topic in a channel. This
            command may fail, and this function cannot tell you due to IRC's
            asynchronous nature.

        :param channel:
            Channel to set the topic in. This can be either a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance or a
            string.

        :param topic:
            Topic to set in channel. Will unset the topic if set to None or
            the empty string.
        """
        if hasattr(channel, "name"):
            channel = channel.name

        if topic is None:
            topic = ''

        self.send("TOPIC", [channel, topic])

    def mode_params(self, add, mode, target, *args):
        """Set modes on a channel with a given target list.

        This is suitable for mass bans/unbans, special status modes, and more.

        :param add:
            Whether or not mode is being added or removed

        :param mode:
            Mode to apply to channel.

        :param target:
            Channel to apply the modes in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance,
            :py:class:`~PyIRC.extensions.usertrack.User` instance, or a
            string.

        :param \*args:
            Targets or params for modes. Can be either
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.
        """
        if not args:
            raise ValueError("args are needed for this function")

        if len(mode) > 1:
            raise ValueError("Only one mode may be set by this function")

        if hasattr(target, "name"):
            target = target.name
        elif hasattr(target, "nick"):
            target = target.nick

        params = []
        for param in args:
            if hasattr(target, "nick"):
                # Map User instances into nicks
                param = param.nick

            params.append(param)

        isupport = self.get_extension("ISupport")
        if isupport:
            modes = isupport.get("MODES")
            if modes:
                modes = int(modes)
            else:
                # Be conservative
                modes = 4

            if modes > 8:
                # Insanity...
                modes = 8

        groups = (params[n:n + modes] for n in range(0, len(params), modes))
        flag = '+' if add else '-'
        for group in groups:
            modes = flag + (mode * len(group))
            params = [channel, flag + (mode * len(group))]
            params.extend(group)
            self.send("MODE", params)

    def op(self, channel, *args):
        """Op a user (or users) on a given channel.

        :param channel:
            Channel to op the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to op. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.
        """
        if not args:
            raise ValueError("args are needed for this function")

        self.mode_params(True, 'o', channel, *args)

    def deop(self, channel, *args):
        """Deop a user (or users) on a given channel.

        :param channel:
            Channel to deopop the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to deop. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.
        """
        if not args:
            raise ValueError("args are needed for this function")

        self.mode_params(False, 'o', channel, *args)

    def voice(self, channel, *args):
        """Voice a user (or users) on a given channel.

        :param channel:
            Channel to voice the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to voice. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.
        """
        if not args:
            raise ValueError("args are needed for this function")

        self.mode_params(True, 'v', channel, *args)

    def devoice(self, channel, *args):
        """Devoice a user (or users) on a given channel.

        :param channel:
            Channel to devoice the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to devoice. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.
        """
        if not args:
            raise ValueError("args are needed for this function")

        self.mode_params(False, 'v', channel, *args)

    def halfop(self, channel, *args):
        """Halfop a user (or users) on a given channel.

        This may not be supported by your IRC server. Notably, FreeNode,
        EfNet, and IRCNet do not support this.

        :param channel:
            Channel to halfop the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to halfop. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.
        """
        if not args:
            raise ValueError("args are needed for this function")

        self.mode_params(True, 'h', channel, *args)

    def dehalfop(self, channel, *args):
        """Dehalfop a user (or users) on a given channel.

        This may not be supported by your IRC server. Notably, FreeNode,
        EfNet, and IRCNet do not support this.

        :param channel:
            Channel to dehalfop the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to dehalfop. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.
        """
        if not args:
            raise ValueError("args are needed for this function")

        self.mode_params(False, 'h', channel, *args)

    def process_bantargs(self, *args):
        """Process ban targets (as used by ban modes).

        .. note::
            The default mask format is $a:account if an account is available
            for the user. This only works on servers that support extended
            bans. The fallback is ``*!*@host``. This may not be suitable for
            all uses. It is recommended more advanced users use strings
            instead of User instances.
        """
        if not args:
            raise ValueError("args are needed for this function")

        isupport = self.get_extension("ISupport")
        if not isupport:
            extbans = False
        else:
            extban = isupport.get("EXTBAN")
            if extban[0] != '$' or 'a' not in extban[1]:
                extbans = False
            else:
                extbans = True

        # Preprocess strings
        params = []
        for param in args:
            if not hasattr(param, "nick"):
                params.append(param)
                continue

            if extbans and param.account:
                param = "$a:{}".format(param.account)
            else:
                param = "*!*@{}".format(param.host)

            params.append(param)

        return params

    def ban(self, channel, *args):
        """Ban a user (or users) on a given channel.

        :param channel:
            Channel to ban the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to ban. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.

        .. note::
            All items are passed through :meth:`process_bantargs`.
        """
        self.mode_params(True, 'b', channel, *self.process_bantargs(*args))

    def unban(self, channel, *args):
        """Unban a user (or users) on a given channel.

        Note at present this is not reliable if User instances are passed in.
        This is an unfortunate side effect of the way IRC works (ban masks may
        be freeform). Another extension may provide enhanced capability to
        do this in the future.

        :param channel:
            Channel to unban the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to unban. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.

        .. note::
            All items are passed through :meth:`process_bantargs`.
        """
        self.mode_params(False, 'b', channel, *self.process_bantargs(*args))

    def banexempt(self, channel, *args):
        """Exempt a user (or users) from being banned on a given channel.

        Most (but not all) servers support this. IRCNet notably does not.

        :param channel:
            Channel to ban exempt the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to ban exempt. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.

        .. note::
            All items are passed through :meth:`process_bantargs`.
        """
        isupport = self.get_extension("ISupport")
        if isupport and not (isupport.get("EXCEPTS") or 'e' in
                             isupport.get("CHANMODES")[0]):
            return False

        self.mode_params(True, 'e', channel, *self.process_bantargs(*args))

    def unbanexempt(self, channel, *args):
        """Un-exempt a user (or users) from being banned on a given channel.

        Most (but not all) servers support this. IRCNet notably does not.

        Note at present this is not reliable if User instances are passed in.
        This is an unfortunate side effect of the way IRC works (ban masks may
        be freeform). Another extension may provide enhanced capability to
        do this in the future.

        :param channel:
            Channel to un-ban exempt the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to un-ban exempt. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.

        .. note::
            All items are passed through :meth:`process_bantargs`.
        """
        isupport = self.get_extension("ISupport")
        if isupport and not (isupport.get("EXCEPTS") or 'e' in
                             isupport.get("CHANMODES")[0]):
            return False

        self.mode_params(False, 'e', channel, *self.process_bantargs(*args))

    def inviteexempt(self, channel, *args):
        """Invite exempt a user (or users) on a given channel.

        Most (but not all) servers support this. IRCNet notably does not.

        :param channel:
            Channel to ban exempt the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to invite exempt. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.

        .. note::
            All items are passed through :meth:`process_bantargs`.
        """
        isupport = self.get_extension("ISupport")
        if isupport and not (isupport.get("EXCEPTS") or 'I' in
                             isupport.get("CHANMODES")[0]):
            return False

        self.mode_params(True, 'I', channel, *self.process_bantargs(*args))

    def uninviteexempt(self, channel, *args):
        """Un-invite exempt a user (or users) on a given channel.

        Most (but not all) servers support this. IRCNet notably does not.

        Note at present this is not reliable if User instances are passed in.
        This is an unfortunate side effect of the way IRC works (masks may be
        freeform). Another extension may provide enhanced capability to do this
        in the future.

        :param channel:
            Channel to un-invite exempt the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to un-invite exempt. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.

        .. note::
            All items are passed through :meth:`process_bantargs`.
        """
        isupport = self.get_extension("ISupport")
        if isupport and not (isupport.get("EXCEPTS") or 'I' in
                             isupport.get("CHANMODES")[0]):
            return False

        self.mode_params(False, 'I', channel, *self.process_bantargs(*args))

    def quiet(self, channel, *args):
        """Quiet a user (or users) on a given channel.

        Many servers do not support this. This supports the charybdis-derived
        variant. This means it will work on Charybdis and ircd-seven networks
        (notably FreeNode) but few others.

        InspIRCd and (UnrealIRCd) support will come eventually.

        This **requires** :py:class:`~PyIRC.extensions.isupport.ISupport` be
        enabled, to disambiguate quiet from owner on UnrealIRCd and InspIRCd.

        :param channel:
            Channel to quiet the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to quiet. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.

        .. note::
            All items are passed through :meth:`process_bantargs`.
        """
        isupport = self.get_extension("ISupport")
        if not isupport:
            return False

        if 'q' not in isupport.get("CHANMODES")[0]:
            return False

        if 'q' in isupport.get('PREFIX'):
            # Nope! It's owner here! RUN AWAY!!!
            return False

        self.mode_params(True, 'q', channel, *self.process_bantargs(*args))

    def unquiet(self, channel, *args):
        """Unquiet a user (or users) on a given channel.

        Many servers do not support this. This supports the charybdis-derived
        variant. This means it will work on Charybdis and ircd-seven networks
        (notably FreeNode) but few others.

        InspIRCd and (UnrealIRCd) support will come eventually.

        This **requires** :py:class:`~PyIRC.extensions.isupport.ISupport` be
        enabled, to disambiguate quiet from owner on UnrealIRCd and InspIRCd.

        Note at present this is not reliable if
        :py:class:`~PyIRC.extensions.usertrack.User` instances are passed in.
        This is an unfortunate side effect of the way IRC works (masks may be
        freeform). Another extension may provide enhanced capability to do this
        in the future.

        :param channel:
            Channel to unquiet the user or users in. This can be a
            :py:class:`~PyIRC.extensions.channeltrack.Channel` instance, or a
            string.

        :param \*args:
            Users to unquiet. Can be
            :py:class:`~PyIRC.extensions.usertrack.User` instances or strings.

        .. note::
            All items are passed through :meth:`process_bantargs`.
        """
        isupport = self.get_extension("ISupport")
        if not isupport:
            return False

        if 'q' not in isupport.get("CHANMODES")[0]:
            return False

        if 'q' in isupport.get('PREFIX'):
            # Nope! It's owner here! RUN AWAY!!!
            return False

        self.mode_params(False, 'q', channel, *self.process_bantargs(*args))
