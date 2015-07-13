#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Base tracking API.

This is not really meant for direct use; it converts commands into
events for ingestion into the other tracking components.

"""


from collections import namedtuple
from logging import getLogger
from time import time

from taillight.signal import Signal

from PyIRC.base import event
from PyIRC.auxparse import mode_parse, prefix_parse, status_prefix_parse
from PyIRC.extension import BaseExtension
from PyIRC.line import Hostmask
from PyIRC.numerics import Numerics


_logger = getLogger(__name__)


Mode = namedtuple("Mode", "mode param adding timestamp")
"""A mode being added or removed"""


class Scope:
    """A scope object passed to receivers of scope events.

    :param target:
        The :py:class:`~PyIRC.line.Hostmask` of user that is changing scope.

    :param scope:
        Scope of the change, None for global, or set to a channel.

    :param leaving:
        whether or not the user is leaving, may be ``none`` for not
        applicable.

    :param reason:
        The reason for the change (part/kick reason).

    :param gecos:
        The GECOS of the user changing scope, may be ``none``.

    :param account:
        The account of the user changing scope, may be ``none``.

    :param modes:
        The modes of the user that are being explicitly added or removed by
        scope change.

    :param cause:
        The user that caused this change (for kicks, etc).

    """

    __slots__ = ["target", "scope", "leaving", "reason", "gecos", "account",
                 "modes", "cause"]

    def __init__(self, target, scope=None, leaving=None, reason=None,
                 gecos=None, account=None, modes=[], cause=None):
        self.scope = scope
        self.leaving = leaving
        self.reason = reason
        self.gecos = gecos
        self.account = account
        self.modes = modes
        self.cause = cause


class BaseTrack(BaseExtension):

    """Base tracking extension, providing events for other tracking extensions.

    This extension adds ``base.base_track`` as itself as an alias for
    ``get_extension("BaseTrack").``.

    """

    caps = {
        "extended-join": [],
        "multi-prefix": [],
        "userhost-in-names": [],
    }

    requires = ["ISupport"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base.base_track = self

        self.sent_protoctl = False

    @event("commands", "JOIN")
    def join(self, caller, line):
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

        scope = Scope(hostmask, channel, False, gecos=gecos, account=account)
        self.call_event("scope", "user_join", scope)

    @event("commands", Numerics.RPL_NAMREPLY)
    def names(self, caller, line):
        params = line.params

        channel = params[2]

        isupport = self.base.isupport
        prefix = prefix_parse(isupport.get("PREFIX"))

        for hostmask in params[3].split(' '):
            if not hostmask:
                continue

            modes, hostmask = status_prefix_parse(hostmask, prefix)
            hostmask = Hostmask.parse(hostmask)

            modes = [(m, hostmask, True, None) for m in modes]

            scope = Scope(hostmask, channel, False, cause=line.hostmask, modes=modes)
            self.call_event("scope", "user_burst", scope)

    @event("commands", "PART")
    def part(self, caller, line):
        params = line.params

        channel = params[0]
        reason = (params[1] if len(params) > 1 else None)

        scope = Scope(line.hostmask, channel, True, reason=reason,
                      cause=line.hostmask)
        self.call_event("scope", "user_part", scope)

    @event("commands", "KICK")
    def kick(self, caller, line):
        params = line.params

        channel = params[0]
        target = Hostmask(nick=params[1])
        reason = params[2]

        scope = Scope(target, channel, True, reason=reason,
                      cause=line.hostmask)
        self.call_event("scope", "user_kick", scope)

    @event("commands", "QUIT")
    def quit(self, caller, line):
        params = line.params

        reason = params[0] if params else None

        # TODO - KILL events
        scope = Scope(line.hostmask, None, True, reason=reason,
                      cause=line.hostmask)
        self.call_event("scope", "user_quit", scope)

    @event("commands", Numerics.RPL_CHANNELMODEIS)
    @event("commands", "MODE")
    def mode(self, caller, line):
        # Offer an easy to use interface for mode
        isupport = self.base.isupport
        modegroups = isupport.get("CHANMODES")
        prefix = prefix_parse(isupport.get("PREFIX"))

        params = line.params[:] if line.command == "MODE" else line.params[1:]

        target = params[0]
        modes = params[1]
        params = params[2:]

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
            mode = Mode(mode, param, adding, None)
            self.call_event("modes", mode_call, line.hostmask, target, mode)

    @event("commands", Numerics.RPL_ENDOFMOTD)
    @event("commands", Numerics.ERR_NOMOTD)
    def send_protoctl(self, caller, line):
        # Send the PROTOCTL NAMESX/UHNAMES stuff if we have to
        if self.sent_protoctl:
            return

        isupport = self.base.isupport

        protoctl = []
        if isupport.get("UHNAMES"):
            protoctl.append("UHNAMES")

        if isupport.get("NAMESX"):
            protoctl.append("NAMESX")

        if protoctl:
            self.send("PROTOCTL", protoctl)

        self.sent_protoctl = True

    @event("commands", Numerics.RPL_BANLIST)
    def ban_list(self, caller, line):
        return self.handle_list(line, 'b')

    @event("commands", Numerics.RPL_EXCEPTLIST)
    def except_list(self, caller, line):
        return self.handle_list(line, 'e')

    @event("commands", Numerics.RPL_INVITELIST)
    def invite_list(self, caller, line):
        return self.handle_list(line, 'I')

    @event("commands", Numerics.RPL_QUIETLIST)
    def quiet_list(self, caller, line):
        isupport = self.base.isupport
        if 'q' in isupport.get("PREFIX"):
            _logger.critical("Got a quiet mode, but mode for quiet is " \
                             "unknown to us!")
            _logger.critical("Please report a bug to the PyIRC team with " \
                             "the mode your IRC daemon uses, along with its " \
                             "version information")
            return

        return self.handle_list(line, 'q')

    @event("commands", Numerics.RPL_SPAMFILTERLIST)
    def spamfilter_list(self, caller, line):
        return self.handle_list(line, 'g')

    @event("commands", Numerics.RPL_EXEMPTCHANOPSLIST)
    def exemptchanops_list(self, caller, line):
        return self.handle_list(line, 'X')

    @event("commands", Numerics.RPL_AUTOOPLIST)
    def autoop_list(self, caller, line):
        return self.handle_list(line, 'w')

    @event("commands", Numerics.RPL_REOPLIST)
    def reop_list(self, caller, line):
        return self.handle_list(line, 'R')

    def handle_list(self, line, mode):
        params = line.params

        try:
            target = params[1]
            mask = params[2]
            if len(params) > 3:
                setter = Hostmask.parse(params[3])
                if len(params) > 4:
                    timestamp = int(params[4])
            else:
                setter = line.hostmask
                timestamp = None
        except Exception as e:
            _logger.warning("Bogus list mode received: %s (exception: %s)",
                            mode, e)
            return

        mode = Mode(mode, mask, True, timestamp)
        self.call_event("modes", "mode_list", setter, target, mode)
