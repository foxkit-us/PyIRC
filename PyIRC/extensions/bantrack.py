#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Track IRC ban modes (+beIq)

In order to be taught about new types, this extension must know the
numerics used for ban listing.

"""


from collections import namedtuple
from logging import getLogger


from PyIRC.signal import event
from PyIRC.extensions import BaseExtension
from PyIRC.numerics import Numerics


_logger = getLogger(__name__)  # pylint: disable=invalid-name


BanEntry = namedtuple("BanEntry", "string setter timestamp")


class BanTrack(BaseExtension):

    """Track bans and other "list" modes.

    This augments the :py:class:`~PyIRC.extensions.channeltrack.ChannelTrack`
    extension.

    Although the actual reporting is done by
    :py:class:`~PyIRC.extensions.basetrack.BaseTrack`, this helps with
    the actual retrieval of the modes, and setting synched states.

    .. note::
        Unless you are opped, your view of modes such as +eI may be limited
        and incomplete.

    """

    requires = ["ISupport", "ChannelTrack", "BasicRFC"]

    @event("channel", "channel_create")
    def join(self, _, channel):
        _logger.debug("Creating ban modes for channel %s",
                      channel.name)

        channel.synced_list = dict()

        isupport = self.base.isupport
        modes = isupport.get("CHANMODES")[0]

        for mode in modes:
            channel.modes[mode] = list()
            channel.synced_list[mode] = False

        self.send("MODE", [channel.name, modes])

    @event("modes", "mode_list")
    def mode_list(self, _, setter, target, mode):
        if mode.param is None:
            return

        channeltrack = self.base.channel_track
        channel = channeltrack.get_channel(target)
        if not channel:
            # Not a channel or we don't know about it.
            return

        modes = channel.modes[mode.mode]

        entry = BanEntry(mode.param, setter, mode.timestamp)

        # Check for existing ban
        for i, (string, _, _) in enumerate(list(modes)):
            if self.casecmp(mode.param, string):
                if mode.adding:
                    # Update timestamp and setter
                    _logger.debug("Replacing entry: %r -> %r",
                                  modes[i], entry)
                    modes[i] = entry
                else:
                    # Delete ban
                    _logger.debug("Removing ban: %r", modes[i])
                    del modes[i]

                return

        _logger.debug("Adding entry: %r", entry)
        modes.append(entry)

    @event("modes", "mode_prefix")
    def mode_prefix(self, _, setter, target, mode):
        if mode.mode == 'v':
            # Voice, don't care
            return

        basicrfc = self.base.basic_rfc
        if not self.casecmp(mode.param, basicrfc.nick):
            # Not us, don't care
            return

        channeltrack = self.base.channel_track
        channel = channeltrack.get_channel(target)
        if not channel:
            # Not a channel or we don't know about it.
            return

        if mode.adding:
            check = ''
            for sync, value in channel.synced_list.items():
                if not value:
                    check += sync

            if check:
                self.send("MODE", [target, check])

    @event("commands", Numerics.RPL_ENDOFBANLIST)
    def end_ban(self, _, line):
        self.set_synced(line, 'b')

    @event("commands", Numerics.RPL_ENDOFEXCEPTLIST)
    def end_except(self, _, line):
        self.set_synced(line, 'e')

    @event("commands", Numerics.RPL_ENDOFINVEXLIST)
    def end_invex(self, _, line):
        self.set_synced(line, 'I')

    @event("commands", Numerics.RPL_ENDOFQUIETLIST)
    def end_quiet(self, _, line):
        self.set_synced(line, 'q')

    @event("commands", Numerics.ERR_ENDOFSPAMFILTERLIST)
    def end_spamfilter(self, _, line):
        self.set_synced(line, 'g')

    @event("commands", Numerics.ERR_ENDOFEXEMPTCHANOPSLIST)
    def end_exemptchanops(self, _, line):
        self.set_synced(line, 'X')

    @event("commands", Numerics.RPL_ENDOFREOPLIST)
    def end_reop(self, _, line):
        self.set_synced(line, 'R')

    @event("commands", Numerics.RPL_ENDOFAUTOOPLIST)
    def end_autoop(self, _, line):
        self.set_synced(line, 'w')

    def set_synced(self, line, mode):
        channeltrack = self.base.channel_track
        channel = channeltrack.get_channel(line.params[1])
        if not channel:
            # Not a channel or we don't know about it.
            return

        if mode not in channel.synced_list:
            _logger.warning("Got bogus/invalid end of list sync for mode %s",
                            mode)
            return

        channel.synced_list[mode] = True
