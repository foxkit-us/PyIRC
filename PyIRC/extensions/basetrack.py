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

from PyIRC.extension import BaseExtension
from PyIRC.line import Hostmask
from PyIRC.hook import hook, PRIORITY_FIRST
from PyIRC.event import Event, EventState
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


Mode = namedtuple("Mode", "mode param adding")
"""A mode being added or removed"""


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


class BaseTracking(BaseExtension):

    """Base tracking extension, providing events for other tracking
    extensions."""

    hook_classes = {
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

