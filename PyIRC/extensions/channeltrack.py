# Copyright © 2013-2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


""" Track channels that we have joined and their associated data

This data includes ops, modes, the topic, and associated data.
"""


from time import time
from functools import partial
from logging import getLogger

from PyIRC.casemapping import IRCDict
from PyIRC.extension import BaseExtension
from PyIRC.hook import hook
from PyIRC.line import Hostmask
from PyIRC.numerics import Numerics
from PyIRC.auxparse import mode_parse, prefix_parse, status_prefix_parse


logger = getLogger(__name__)


class Channel:

    """ A channel entity """

    def __init__(self, case, name, **kwargs):
        """Store the data for a channel.

        Unknown values are stored as None, whereas empty ones are stored as
        '' or 0, so take care in comparisons involving values from this class.

        Keyword arguments:

        name
            Name of the channel, not casemapped.

        topic
            The channel topic.

        topictime
            Time the channel topic was set, in Unix time.

        topicwho
            Who set the topic, as a freeform string.

        users
            A mapping containing user to their channel status modes.

        timestamp
            Timestamp of the channel (channel creation), in Unix time.

        url
            URL of the channel, sent on some IRC servers.
        """
        if name is None:
            raise ValueError("name must not be None")
        self.name = name

        self.modes = kwargs.get("modes", dict())
        self.topic = kwargs.get("topic", None)
        self.topictime = kwargs.get("topictime", None)
        self.topicwho = kwargs.get("topicwho", None)
        self.timestamp = kwargs.get("timestamp", None)
        self.url = kwargs.get("url", None)
        self.users = kwargs.get("users", IRCDict(case))


class ChannelTrack(BaseExtension):

    """ Tracks channels and the users on the channels.

    Only the user's casemapped nicks are stored, as well as their statuses.
    They are stored casemapped to make it easier to look them up in other
    extensions.

    The following attribute is publicly available:

    channels
        Mapping of channels, where the keys are casemapped channel names, and
        the values are Channel instances.

    For more elaborate user tracking, see usertrack.UserTrack. """

    caps = {
        "multi-prefix" : [],
    }

    requires = ["ISupport"]

    def __init__(self, base, **kwargs):
        self.base = base

        # Our channel set
        self.channels = IRCDict(self.case)

        # Scheduled items
        self.mode_timers = IRCDict(self.case)

    def get_channel(self, name):
        """Retrieve a channel from the tracking dictionary based on name.

        Use of this method is preferred to directly accessing the channels
        dictionary.

        Returns None if channel not found.

        Arguments:

        name
            Name of the channel to retrieve.
        """

        return self.channels.get(name)

    def add_channel(self, name, **kwargs):
        """Add a channel to the tracking dictionary.

        Avoid using this method directly unless you know what you are doing.
        """
        channel = self.get_channel(name)
        if channel is None:
            logger.debug("Adding channel: %s", name)

            channel = Channel(self.base.case, name, **kwargs)
            self.channels[name] = channel

        return channel

    def remove_channel(self, name):
        """Remove a channel from the tracking dictionary.

        Avoid using this method directly unless you know what you are doing.
        """

        channel = self.get_channel(name)
        if not channel:
            return

        del self.channels[name]

    @hook("hooks", "case_change")
    def case_change(self, event):
        self.channels = self.channels.convert(self.base.case)
        self.mode_timers = self.mode_timers.convert(self.base.case)

    @hook("hooks", "disconnected")
    def close(self, event):
        self.channels.clear()
        for timer in self.mode_timers.values():
            try:
                self.unschedule(timer)
            except ValueError:
                pass

    @hook("commands", "JOIN")
    def join(self, event):
        hostmask = event.line.hostmask
        channel = self.get_channel(event.line.params[0])
        if not channel:
            # We are joining
            channel = self.add_channel(event.line.params[0])

        channel.users[hostmask.nick] = set()

    @hook("commands", "KICK")
    @hook("commands", "PART")
    def part(self, event):
        hostmask = event.line.hostmask
        channel = self.get_channel(event.line.params[0])
        assert channel

        basicrfc = self.get_extension("BasicRFC")

        if self.casecmp(hostmask.nick, basicrfc.nick):
            # We are leaving
            self.remove_channel(channel.name)
            timer = self.mode_timers.pop(channel.name, None)
            if timer is not None:
                try:
                    self.unschedule(timer)
                except ValueError:
                    pass
            return

        del channel.users[hostmask.nick]

    def _get_modegroups(self):
        isupport = self.get_extension("ISupport")
        modes = isupport.get("CHANMODES")
        return list(modes)

    @hook("commands", "MODE")
    def mode(self, event):
        channel = self.get_channel(event.line.params[0])
        if not channel:
            return

        isupport = self.get_extension("ISupport")

        # Build mode groups
        modegroups = self._get_modegroups()

        # Status modes
        prefix = prefix_parse(isupport.get("PREFIX"))

        modes = event.line.params[1]
        if len(event.line.params) >= 3:
            params = event.line.params[2:]
        else:
            params = []
        for mode, param, adding in mode_parse(modes, params, modegroups, prefix):
            if mode in prefix:
                user = channel.users[param]
                if adding:
                    logger.debug("Adding mode for nick %s: %s", param, mode)
                    user.add(mode)
                else:
                    logger.debug("Removing mode for nick %s: %s", param, mode)
                    user.discard(mode)

                continue
            elif mode in modegroups[0]:
                # We don't do list modes because getting a full list may not
                # be possible in all channels due to restrictions/ircd config,
                # so any tracking will be misleading.
                # Another extension could easily support it.
                continue

            if adding:
                channel.modes[mode] = param
                logger.debug("Adding mode %s (%s)", mode, param)
            else:
                channel.modes.pop(mode, None)
                logger.debug("Removing mode %s (%s)", mode, param)

    @hook("commands", Numerics.RPL_CHANNELMODEIS)
    def channel_modes(self, event):
        channel = self.get_channel(event.line.params[1])
        if not channel:
            return

        isupport = self.get_extension("ISupport")

        # Build mode groups
        modegroups = self._get_modegroups()

        # Status modes
        prefix = prefix_parse(isupport.get("PREFIX"))

        modes = event.line.params[2]
        if len(event.line.params) >= 4:
            params = event.line.params[3:]
        else:
            params = []
        for mode, param, adding in mode_parse(modes, params, modegroups, prefix):
            if mode in prefix:
                user = channel.users[param]
                if adding:
                    logger.debug("Adding mode %s to %s in %s", mode, param, channel)
                    user.add(mode)
                else:
                    logger.debug("Removing mode %s from %s in %s", mode,
                                 param, channel)
                    user.discard(mode)

                continue
            elif mode in modegroups[0]:
                # We shouldn't get these here...
                logger.warning("Unexpected mode with channel mode numeric: " \
                               "%s%s (%s)", "+" if adding else "-", mode, param)
                continue

            if adding:
                logger.debug("Adding mode %s (%s)", mode, param)
                channel.modes[mode] = param
            else:
                logger.debug("Removing mode %s (%s)", mode, param)
                channel.modes.pop(mode, None)

    @hook("commands", Numerics.RPL_TOPIC)
    @hook("commands", "TOPIC")
    def topic(self, event):
        channel = self.get_channel(event.line.params[0])
        if not channel:
            return

        if event.line.command.lower() == "topic":
            channel = self.get_channel(event.line.params[0])

            # TODO server/local time deltas for more accurate timestamps
            channel.topicwho = line.hostmask
            channel.topictime = int(time())
        else:
            channel = self.get_channel(event.line.params[1])

        channel.topic = event.line.params[-1]

    @hook("commands", Numerics.RPL_NOTOPIC)
    def no_topic(self, event):
        channel = self.get_channel(event.line.params[0])
        if not channel:
            return

        channel.topic = ''

    @hook("commands", Numerics.RPL_TOPICWHOTIME)
    def topic_who_time(self, event):
        channel = self.get_channel(event.line.params[0])
        if not channel:
            return

        channel.topicwho = Hostmask.parse(event.line.params[2])
        channel.topictime = int(event.line.params[3])

    @hook("commands", Numerics.RPL_CHANNELURL)
    def url(self, event):
        channel = self.get_channel(event.line.params[1])
        if not channel:
            return

        channel.url = event.line.params[-1]

    @hook("commands", Numerics.RPL_CREATIONTIME)
    def timestamp(self, event):
        channel = self.get_channel(event.line.params[1])
        if not channel:
            return

        channel.timestamp = int(event.line.params[-1])

        # Cancel
        timer = self.mode_timers.pop(channel.name, None)
        if timer is not None:
            try:
                self.unschedule(timer)
            except ValueError:
                pass

    @hook("commands", Numerics.RPL_NAMREPLY)
    def names(self, event):
        channel = self.get_channel(event.line.params[2])
        if not channel:
            logger.warning("Got NAMES for a channel we don't know about: %s",
                           event.line.params[2])
            return

        isupport = self.get_extension("ISupport")
        prefix = prefix_parse(isupport.get("PREFIX"))

        for nick in event.line.params[-1].split():
            mode, nick = status_prefix_parse(nick, prefix)

            # userhost-in-names is why we do this dance
            nick = Hostmask.parse(nick).nick
            if nick not in channel.users:
                channel.users[nick] = set()

            logger.debug("Adding user %s with modes %r", nick, mode)

            channel.users[nick].update(mode)

    @hook("commands", Numerics.RPL_ENDOFNAMES)
    def names_end(self, event):
        channel = self.get_channel(event.line.params[1])
        if not channel:
            return

        timer = self.schedule(5, partial(self.send, "MODE",
                                         [event.line.params[1]]))
        self.mode_timers[channel.name] = timer

    @hook("commands", "NICK")
    def nick(self, event):
        oldnick = event.line.hostmask.nick
        newnick = event.line.params[-1]

        # Change the nick in all channels
        for channel in self.channels.values():
            if oldnick not in channel.users:
                continue

            # Change the nick
            channel.users[newnick] = channel.users.pop(oldnick)

    @hook("commands", "QUIT")
    def quit(self, event):
        nick = event.line.hostmask.nick

        for channel in self.channels.values():
            channel.users.pop(nick, None)
