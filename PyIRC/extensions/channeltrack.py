# Copyright © 2013-2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from time import time
from collections import defaultdict
from functools import partial
from logging import getLogger

from PyIRC.extension import BaseExtension
from PyIRC.line import Hostmask
from PyIRC.numerics import Numerics
from PyIRC.auxparse import mode_parse, prefix_parse


logger = getLogger(__name__)


class Channel:

    """ A channel entity. """

    def __init__(self, name, **kwargs):
        self.name = name

        self.modes = kwargs.get("modes", dict())
        self.topic = kwargs.get("topic", None)
        self.topictime = kwargs.get("topictime", None)
        self.topicwho = kwargs.get("topicwho", None)
        self.users = kwargs.get("user", dict())
        self.timestamp = kwargs.get("timestamp", None)
        self.url = kwargs.get("url", None)


class ChannelTrack(BaseExtension):

    """ Tracks channels and the like """

    caps = {
        "multi-prefix" : [],
    }

    requires = ["ISupport"]

    def __init__(self, base, **kwargs):

        self.base = base

        self.commands = {
            "JOIN" : self.join,
            "KICK" : self.part,
            "MODE" : self.mode,
            "NICK" : self.nick,
            "PART" : self.part,
            "QUIT" : self.quit,
            "TOPIC" : self.topic,
            Numerics.RPL_CHANNELMODEIS : self.channel_modes,
            Numerics.RPL_CHANNELURL : self.url,
            Numerics.RPL_CREATIONTIME : self.timestamp,
            Numerics.RPL_NOTOPIC : self.no_topic,
            Numerics.RPL_NAMREPLY : self.names,
            Numerics.RPL_TOPIC : self.topic,
            Numerics.RPL_TOPICWHOTIME : self.topic_who_time,
            Numerics.RPL_ENDOFNAMES : self.names_end,
        }

        self.hooks = {
            "disconnected" : self.close,
        }

        # Our channel set
        self.channels = dict()

        # Scheduled items
        self.mode_timers = dict()

    def get_channel(self, name):
        """ Get the Channel instance associated with a channel name """

        return self.channels.get(self.casefold(name))

    def add_channel(self, name, **kwargs):
        """ Add a channel to our list """

        channel = self.get_channel(name)
        if channel is None:
            logger.debug("Adding channel: %s", name)

            channel = Channel(name, **kwargs)
            self.channels[self.casefold(name)] = channel

        return channel

    def remove_channel(self, name):
        """ Remove a channel from our list """

        channel = self.get_channel(name)
        if not channel:
            return

        del self.channels[self.casefold(name)]

    def close(self, event):
        """ Disconnecting from server """

        self.channels.clear()
        for timer in self.mode_timers.values():
            try:
                self.unschedule(timer)
            except ValueError:
                pass

    def join(self, event):
        """ Track a channel JOIN event """

        hostmask = event.line.hostmask
        channel = self.get_channel(event.line.params[0])
        if not channel:
            # We are joining
            assert (self.casefold(hostmask.nick) ==
                    self.casefold(self.base.nick))

            channel = self.add_channel(event.line.params[0])
        
        channel.users[self.casefold(hostmask.nick)] = set()

    def part(self, event):
        """ Track a channel PART event """

        hostmask = event.line.hostmask
        channel = self.get_channel(event.line.params[0])
        assert channel

        if (self.casefold(hostmask.nick) ==
                self.casefold(self.base.nick)):
            # We are leaving
            self.remove_channel(channel.name)
            timer = self.mode_timers.pop(self.casefold(channel.name),
                                         None)
            if timer is not None:
                try:
                    self.unschedule(timer)
                except ValueError:
                    pass
            return

        del channel.users[self.casefold(hostmask.nick)]

    def mode(self, event):
        """ Track a channel MODE effect """

        channel = self.get_channel(event.line.params[0])
        if not channel:
            return

        isupport = self.get_extension("ISupport")

        # Build mode groups
        modegroups = list(isupport.supported.get("CHANMODES",
                                                 ["b", "k", "l", "imnstp"]))

        # Status modes
        prefix = prefix_parse(isupport.supported.get("PREFIX", "(ov)@+"))

        # Parse status modes like list modes
        modegroups[0] += ''.join(prefix.keys())

        modes = event.line.params[1]
        if len(event.line.params) >= 3:
            params = event.line.params[2:]
        else:
            params = []
        for mode, param, adding in mode_parse(modes, params, modegroups):
            if mode in prefix:
                user = channel.users[self.casefold(param)]
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

    def channel_modes(self, event):
        """ Process the RPL_CHANNELMODEIS numeric """

        channel = self.get_channel(event.line.params[1])
        if not channel:
            return
        
        isupport = self.get_extension("ISupport")

        # Build mode groups
        modegroups = list(isupport.supported.get("CHANMODES",
                                                 ["b", "k", "l", "imnstp"]))

        # Status modes
        prefix = prefix_parse(isupport.supported.get("PREFIX", "(ov)@+"))

        # Parse status modes like list modes
        modegroups[0] += ''.join(prefix.keys())

        modes = event.line.params[2]
        if len(event.line.params) >= 4:
            params = event.line.params[3:]
        else:
            params = []
        for mode, param, adding in mode_parse(modes, params, modegroups):
            if mode in prefix:
                user = channel.users[self.casefold(param)]
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

    def topic(self, event):
        """ Process a TOPIC command """

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

    def no_topic(self, event):
        """ Process the numeric symbolising no topic """
        
        channel = self.get_channel(event.line.params[0])
        if not channel:
            return

        channel.topic = ''

    def topic_who_time(self, event):
        """ Process the topic who/time numeric """

        channel = self.get_channel(event.line.params[0])
        if not channel:
            return

        channel.topicwho = Hostmask.parse(event.line.params[2])
        channel.topictime = int(event.line.params[3])

    def url(self, event):
        """ Process a URL numeric """

        channel = self.get_channel(event.line.params[1])
        assert channel

        channel.url = event.line.params[-1]

    def timestamp(self, event):
        """ Process a channel timestamp numeric """

        channel = self.get_channel(event.line.params[1])
        assert channel

        channel.timestamp = int(event.line.params[-1])

        # Cancel
        timer = self.mode_timers.pop(self.casefold(channel.name),
                                     None)
        if timer is not None:
            try:
                self.unschedule(timer)
            except ValueError:
                pass

    def names(self, event):
        """ Process a channel NAMES event """

        channel = self.get_channel(event.line.params[2])
        assert channel

        isupport = self.get_extension("ISupport")
        prefix = prefix_parse(isupport.supported.get("PREFIX", "(ov)@+"))
        pmap = {v : k for k, v in prefix.items()}

        for nick in event.line.params[-1].split():
            mode = set()
            while nick[0] in pmap:
                # Accomodate multi-prefix
                prefix, nick = nick[0], nick[1:]
                mode.add(pmap[prefix])

            # userhost-in-names is why we do this dance
            nick = self.casefold(Hostmask.parse(nick).nick)
            if nick not in channel.users:
                channel.users[nick] = set()

            logger.debug("Adding user %s with modes %r", nick, mode)

            channel.users[nick].update(mode)

    def names_end(self, event):
        """ Process an end of NAMES event """

        channel = self.get_channel(event.line.params[1])
        assert channel

        timer = self.schedule(5, partial(self.send, "MODE",
                                         [event.line.params[1]]))
        self.mode_timers[self.casefold(channel.name)] = timer

    def nick(self, event):
        """ Handle a nick change """

        oldnick = self.casefold(event.line.hostmask.nick)
        newnick = self.casefold(event.line.params[-1])

        # Change the nick in all channels
        for channel in self.channels.values():
            if oldnick not in channel.users:
                continue

            # Change the nick
            channel.users[newnick] = channel.users.pop(oldnick)

    def quit(self, event):
        """ Quit a user """

        nick = self.casefold(event.line.hostmask.nick)

        for channel in self.channels.values():
            channel.users.pop(nick, None)
