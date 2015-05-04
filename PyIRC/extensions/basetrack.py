#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Base tracking API.

This is not really meant for direct use; it converts commands into events for
ingestion into the other tracking components.
"""


from collections import namedtuple
from logging import getLogger
from time import time

from PyIRC.auxparse import mode_parse, prefix_parse, status_prefix_parse
from PyIRC.event import Event, EventState, LineEvent
from PyIRC.extension import BaseExtension
from PyIRC.hook import hook, PRIORITY_FIRST
from PyIRC.line import Hostmask
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


Mode = namedtuple("Mode", "mode param adding")
"""A mode being added or removed"""


class ModeEvent(LineEvent):

    """An event triggered upon mode changes."""

    def __init__(self, event, line, setter, target, adding, mode, param=None,
                 timestamp=None):
        """Initalise the ModeEvent instance.

        Arguments:

        :param event:
            The event fired

        :param line:
            The :py:class:`~PyIRC.line.Line` instance of the firing mode.

        :param setter:
            The :py:class:`~PyIRC.line.Hostmask` of the setter of this mode,
            or ``None`` when unknown.

        :param target:
            The target of this command, as a regular string.

        :param adding:
            Set to ``True`` if the mode is being added to the target, or
            ``False`` if being removed. Consumers should be prepared for
            redundant modes, as many IRC daemons do not do strict checking
            for performance reasons.

        :param mode:
            The mode being set or unset.

        :param param:
            The parameter of the mode, set to ``None`` for most modes.

        :param timestamp:
            The time this mode was set. If None, the current system time will
            be used.
        """
        super().__init__(event, line)

        self.setter = setter
        self.target = target
        self.adding = adding
        self.mode = mode
        self.param = param
        self.timestamp = timestamp if timestamp else round(time())


class TrackEvent(Event):
    
    """Base tracking event"""

    def __init__(self, event, target):
        """Initialise the TrackEvent instance

        :param target:
            Target that is being tracked
        """
        super().__init__(event)
        self.target = target


class ScopeEvent(TrackEvent):

    """User changing scope event"""

    def __init__(self, event, target, scope=None, leaving=None, reason=None,
                 gecos=None, account=None, modes=None, cause=None):
        """Initalise the UserScopeEvent instance

        :param target:
            `~PyIRC.line.Hostmask` of user that is changing scope

        :param scope:
            Scope of the change, None for global, or set to a channel.

        :param leaving:
            Whether or not the user is leaving, may be ``None`` for not
            applicable.

        :param reason:
            Reason for change.

        :param gecos:
            GECOS of the user changing scope, may be ``None``.

        :param account:
            Account of the user changing scope, may be ``None``.

        :param modes:
            Modes of the user that are being explicitly added or removed by
            scope change.

        :param cause:
            User that caused this change.
        """
        super().__init__(event, target)
        self.scope = scope
        self.leaving = leaving
        self.reason = reason
        self.gecos = gecos
        self.account = account
        self.modes = modes
        self.cause = cause


class BaseTrack(BaseExtension):

    """Base tracking extension, providing events for other tracking
    extensions."""

    hook_classes = {
        "mode": ModeEvent,
        "scope": ScopeEvent,
    }

    requires = ["ISupport"]

    @hook("commands", "JOIN", PRIORITY_FIRST)
    def join(self, event):
        line = event.line
        params = line.params

        hostmask = line.hostmask
        if not hostmask:
            return

        channel = params[0]
        account = gecos = None
        if len(params) > 1:
            account = params[1]
            if len(params) > 2:
                gecos = params[2]

        self.call_event("scope", "user_join", hostmask, channel, False,
                        gecos=gecos, account=account)

    @hook("commands", Numerics.RPL_NAMREPLY, PRIORITY_FIRST)
    def names(self, event):
        line = event.line
        params = line.params

        channel = params[2]

        isupport = self.get_extension("ISupport")
        prefix = prefix_parse(isupport.get("PREFIX")) 

        for hostmask in params[3].split(' '):
            if not hostmask:
                continue

            modes, hostmask = status_prefix_parse(nick, prefix)
            hostmask = Hostmask.parse(hostmask)
            
            modes = [(m, hostmask, True) for m in modes]

            self.call_event("scope", "user_burst", hostmask, channel, False,
                            cause=line.hostmask, modes=modes)

    @hook("commands", "PART", PRIORITY_FIRST)
    def part(self, event):
        line = event.line
        params = line.params

        channel = params[0]
        reason = (params[1] if len(params) > 1 else None)

        self.call_event("scope", "user_part", line.hostmask, channel, True,
                        reason=reason, cause=line.hostmask)

    @hook("commands", "KICK", PRIORITY_FIRST)
    def kick(self, event):
        line = event.line
        params = line.params

        channel = params[0]
        target = Hostmask(nick=params[1])
        reason = params[2]

        self.call_event("scope", "user_kick", target, channel, True,
                        reason=reason, cause=line.hostmask)

    @hook("commands", "QUIT", PRIORITY_FIRST)
    def quit(self, event):
        line = event.line
        params = line.params

        reason = params[0] if params else None

        # TODO - KILL events
        self.call_event("scope", "user_quit", line.hostmask, None, True,
                        reason=reason, cause=line.hostmask)

    @hook("commands", Numerics.RPL_CHANNELMODEIS)
    @hook("commands", "MODE")
    def mode(self, event):
        # Offer an easy to use interface for mode
        isupport = self.get_extension("ISupport")
        modegroups = isupport.get("CHANMODES")
        prefix = prefix_parse(isupport.get("PREFIX"))

        line = event.line
        params = list(line.params)
        if line.command == Numerics.RPL_CHANNELMODEIS.value:
            params.pop(0)

        target = params.pop(0)
        modes = params.pop(0)

        channels = tuple(isupport.get("CHANTYPES"))
        if not target.startswith(channels):
            # TODO - user modes
            return

        gen = mode_parse(modes, params, modegroups, prefix)
        prefix = prefix.mode_to_prefix
        for mode, param, adding in gen:
            if mode in prefix:
                mode_call = "mode_prefix"
            elif mode in modegroups[0]:
                mode_call = "mode_list",
            elif mode in modegroups[1]:
                mode_call = "mode_key",
            elif mode in modegroups[2]:
                mode_call = "mode_param",
            else:
                mode_call = "mode_normal"

            # TODO - aggregation
            self.call_event("modes", mode_call, line, line.hostmask, target,
                            adding, mode, param)
