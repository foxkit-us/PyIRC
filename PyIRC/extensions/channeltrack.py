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

    This extension adds ``base.channel_track`` as itself as an alias for
    ``get_extension("ChannelTrack").``.

    channels
        Mapping of channels, where the keys are casemapped channel names, and
        the values are Channel instances.

    For more elaborate user tracking, see
    :py:module::`~PyIRC.extensions.usertrack`."""

    requires = ["BaseTrack", "BasicRFC", "ISupport"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Convenience method
        self.base.channel_track = self

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
            channel.modes[event.mode] = event.param
        else:
            channel.modes.pop(event.mode, None)

    @hook("scope", "user_join")
    def join(self, event):
        # JOIN event
        basicrfc = self.base.basic_rfc
        if self.casecmp(event.target.nick, basicrfc.nick):
            # We're joining
            self.add_channel(event.scope)

        self.burst(event)

    @hook("scope", "user_burst")
    def burst(self, event):
        # NAMES event
        channel = self.get_channel(event.scope)
        if not channel:
            return

        user = event.target.nick

        if user not in channel.users:
            channel.users[user] = set()

        modes = {m[0] for m in event.modes} if event.modes else set()
        channel.users[user] = modes

    @hook("scope", "user_part")
    @hook("scope", "user_kick")
    def part(self, event):
        channel = self.get_channel(event.scope)
        assert channel

        user = event.target.nick

        basicrfc = self.base.basic_rfc
        if self.casecmp(user, basicrfc.nick):
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

        del channel.users[user]

    @hook("scope", "user_quit")
    def quit(self, event):
        user = event.target.nick

        for channel in self.channels.values():
            channel.users.pop(user, None)

    @hook("commands", Numerics.RPL_TOPIC)
    @hook("commands", "TOPIC")
    def topic(self, event):
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
        channel = self.get_channel(event.line.params[1])
        if not channel:
            return

        channel.topic = ''

    @hook("commands", Numerics.RPL_TOPICWHOTIME)
    def topic_who_time(self, event):
        channel = self.get_channel(event.line.params[1])
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

