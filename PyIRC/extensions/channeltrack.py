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

from PyIRC.casemapping import IRCDict, IRCDefaultDict
from PyIRC.extension import BaseExtension
from PyIRC.hook import hook
from PyIRC.line import Hostmask
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


class Channel:

    """ A channel entity """

    def __init__(self, case, name, **kwargs):
        """Store the data for a channel.

        Unknown values are stored as None, whereas empty ones are stored as
        '' or 0, so take care in comparisons involving values from this class.

        Keyword arguments:

        :key name:
            Name of the channel, not casemapped.

        :key topic:
            The channel topic.

        :key topictime:
            Time the channel topic was set, in Unix time.

        :key topicwho:
            Who set the topic, as a freeform string.

        :key users:
            A mapping containing user to their channel status modes.

        :key timestamp:
            Timestamp of the channel (channel creation), in Unix time.

        :key url:
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
        self.users = kwargs.get("users", IRCDefaultDict(case, set))

    def __repr__(self):
        keys = ("modes", "topic", "topictime", "topicwho", "timestamp", "url",
                "users")

        # key={0.key!r}
        rep = ["{0}={{0.{0}!r}}".format(k) for k in keys]

        # Final format
        rep = "Channel({})".format(", ".join(rep))
        return rep.format(self)


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
        "multi-prefix": [],
    }

    requires = ["ISupport", "BaseTrack"]

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

        :param name:
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

            channel = Channel(self.case, name, **kwargs)
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
        self.channels = self.channels.convert(self.case)
        self.mode_timers = self.mode_timers.convert(self.case)

    @hook("hooks", "disconnected")
    def close(self, event):
        self.channels.clear()
        for timer in self.mode_timers.values():
            try:
                self.unschedule(timer)
            except ValueError:
                pass

    @hook("modes", "mode_prefix")
    def prefix(self, event):
        # Parse into hostmask in case of usernames-in-host
        channel = self.get_channel(event.target)
        if not channel:
            logger.warning("Got a PREFIX event for an unknown channel: %s",
                           event.target)
            return

        hostmask = Hostmask.parse(event.param)
        if event.adding:
            channel.users[hostmask.nick].add(event.mode)
        else:
            channel.users[hostmask.nick].discard(event.mode)

    @hook("modes", "mode_key")
    @hook("modes", "mode_param")
    @hook("modes", "mode_normal")
    def modes(self, event):
        channel = self.get_channel(event.target)
        if not channel:
            return

        if event.adding:
            channel.modes[event.param] = event.mode
        else:
            channel.modes.pop(event.param, None)

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

        logger.debug("users before deletion: %r", channel.users)

        del channel.users[hostmask.nick]

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

    @hook("commands", Numerics.RPL_BANLIST)
    def ban_list(self, event):
        return self.handle_list(event, 'b')

    @hook("commands", Numerics.RPL_EXCEPTLIST)
    def except_list(self, event):
        return self.handle_list(event, 'e')

    @hook("commands", Numerics.RPL_INVITELIST)
    def invite_list(self, event):
        return self.handle_list(event, 'I')

    @hook("commands", Numerics.RPL_QUIETLIST)
    def quiet_list(self, event):
        isupport = self.get_extension("ISupport")
        if 'q' in isupport.get("PREFIX"):
            logger.critical("Got a quiet mode, but mode for quiet is " \
                            "unknown to us!")
            logger.critical("Please report a bug to the PyIRC team with " \
                            "the mode your IRC daemon uses, along with its " \
                            "version information")
            return

        return self.handle_list(event, 'q')

    @hook("commands", Numerics.RPL_SPAMFILTERLIST)
    def spamfilter_list(self, event):
        return self.handle_list(event, 'g')

    @hook("commands", Numerics.RPL_EXEMPTCHANOPSLIST)
    def exemptchanops_list(self, event):
        return self.handle_list(event, 'X')

    @hook("commands", Numerics.RPL_AUTOOPLIST)
    def autoop_list(self, event):
        return self.handle_list(event, 'w')

    @hook("commands", Numerics.RPL_REOPLIST)
    def reop_list(self, event):
        return self.handle_list(event, 'R')

    def handle_list(self, event, mode):
        line = event.line
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
            logger.warning("Bogus list mode received: %s (exception: %s)",
                           mode, e)
            return

        self.call_event("modes", "mode_list", line, setter, target, True,
                        mode, mask, timestamp)
