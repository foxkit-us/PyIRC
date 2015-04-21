#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Track IRC ban modes (+beIq)

In order to be taught about new types, this extension must know the numerics
used for ban listing.
"""


from time import time
from collections import namedtuple
from logging import getLogger

from PyIRC.auxparse import mode_parse, prefix_parse
from PyIRC.extension import BaseExtension
from PyIRC.hook import hook, PRIORITY_LAST
from PyIRC.line import Hostmask
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


BanEntry = namedtuple("BanEntry", "string setter timestamp")


class BanTrack(BaseExtension):

    """Track bans and other "list" modes.

    This supports +beI, Inspircd +g, and Charybdis-style +q. Others may be
    added for other IRC daemons in the future.

    .. note::
        Unless you are opped, your view of modes such as +eI may be limited
        and incomplete.
    """

    requires = ["ISupport", "ChannelTrack", "BasicRFC"]

    default_ban_numerics_modes = {
        Numerics.RPL_BANLIST.value: 'b',
        Numerics.RPL_EXCEPTLIST.value: 'e',
        Numerics.RPL_INVITELIST.value: 'I',
        Numerics.RPL_QUIETLIST.value: 'q',
    }

    def __init__(self, base, **kwargs):
        """Arguments:

        ban_numerics_modes
            A mapping of numerics to modes, useful on InspIRCd servers
            A sensible default is used.
        """
        self.base = base

        # Numerics to modes
        self.ban_numerics_modes = kwargs.get('ban_numerics_modes',
                                             self.default_ban_numerics_modes)

    @hook("commands", "JOIN", PRIORITY_LAST)
    def join(self, event):
        params = event.line.params
        logger.debug("Creating ban modes for channel %s",
                     params[0])
        channeltrack = self.get_extension("ChannelTrack")
        channel = channeltrack.get_channel(params[0])

        channel.synced_list = dict()

        isupport = self.get_extension("ISupport")
        modes = isupport.get("CHANMODES")[0]

        for mode in modes:
            channel.modes[mode] = list()
            channel.synced_list[mode] = False

        self.send("MODE", [channel.name, modes])

    @hook("modes", "mode_list")
    def mode_list(self, event):
        line = event.line

        if event.param is None:
            return

        channeltrack = self.get_extension("ChannelTrack")
        channel = channeltrack.get_channel(event.target)
        if not channel:
            # Not a channel or we don't know about it.
            return

        modes = channel.modes[event.mode]

        entry = BanEntry(param, event.setter, event.timestamp)

        # Check for existing ban
        for i, (string, _, _) in enumerate(list(modes[event.mode])):
            if self.casecmp(event.param, string):
                if event.adding:
                    # Update timestamp and setter
                    logger.debug("Replacing entry: %r -> %r",
                                 modes[i], entry)
                    modes[i] = entry
                else:
                    # Delete ban
                    logger.debug("Removing ban: %r", modes[i])
                    del modes[i]

                return

        logger.debug("Adding entry: %r", entry)
        modes.append(entry)

    @hook("modes", "mode_prefix")
    def mode_prefix(self, event):
        if event.mode == 'v':
            # Voice, don't care
            return

        basicrfc = self.get_extension("BasicRFC")
        if not self.casecmp(event.target, basicrfc.nick):
            # Not us, don't care
            return

        channeltrack = self.get_extension("ChannelTrack")
        channel = channeltrack.get_channel(event.target)
        if not channel:
            # Not a channel or we don't know about it.
            return

        if event.adding:
            check = ''
            for sync, value in channel.synced_list.items():
                if not value:
                    check += sync

            if check:
                isupport = self.get_extension("ISupport")
                self.send("MODE", [event.target, check])

    @hook("commands", Numerics.RPL_ENDOFBANLIST)
    def end_ban(self, event):
        self.set_synced(event, 'b')

    @hook("commands", Numerics.RPL_ENDOFEXCEPTLIST)
    def end_except(self, event):
        self.set_synced(event, 'e')

    @hook("commands", Numerics.RPL_ENDOFINVEXLIST)
    def end_invex(self, event):
        self.set_synced(event, 'I')

    @hook("commands", Numerics.RPL_ENDOFQUIETLIST)
    def end_quiet(self, event):
        self.set_synced(event, 'q')

    @hook("commands", Numerics.ERR_ENDOFSPAMFILTERLIST)
    def end_spamfilter(self, event):
        self.set_synced(event, 'g')

    @hook("commands", Numerics.ERR_ENDOFEXEMPTCHANOPSLIST)
    def end_exemptchanops(self, event):
        self.set_synced(event, 'X')

    @hook("commands", Numerics.RPL_ENDOFREOPLIST)
    def end_reop(self, event):
        self.set_synced(event, 'R')

    @hook("commands", Numerics.RPL_ENDOFAUTOOPLIST)
    def end_autoop(self, event):
        self.set_synced(event, 'w')

    def set_synced(self, event, mode):
        channeltrack = self.get_extension("ChannelTrack")
        channel = channeltrack.get_channel(event.params[1])
        if not channel:
            # Not a channel or we don't know about it.
            return

        if mode not in channel.synced_list:
            logger.warning("Got bogus/invalid end of list sync for mode %s",
                           mode)
            return

        channel.synced_list[mode] = True

