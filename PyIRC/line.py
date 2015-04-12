#!/usr/bin/env python3
# Copyright © 2013-2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Objects and utilities related to IRC messages"""


import operator

from itertools import takewhile
from functools import reduce
from logging import getLogger


logger = getLogger(__name__)


class Tags:
    """Stores message tags

    Message tags are a new feature proposed by IRCv3 to add enhanced
    out-of-band data to messages.
    """

    __slots__ = ('tags', 'tagstr')

    def __init__(self, *, tags=None, tagstr=None):
        self.tags = tags
        self.tagstr = tagstr

        if not self.tags:
            self = self.parse(self.tagstr)

    @classmethod
    def parse(cls, raw):
        """Parse a raw tag string into a Tags object.

        Arguments:

        raw
            The raw tags to parse into a Tags object.
        """
        if not raw:
            logger.debug("No tags on this message")
            return

        tags = dict()

        for tag in raw.split(';'):
            key, s, value = tag.partition('=')
            if value == '':
                value = None
            tags[key] = value

        return cls(tags=tags, tagstr=raw)


class Hostmask:
    """ Stores a hostmask

    Hostmasks are used to store sources and destinations in IRC messages.

    >>> repr(Hostmask.parse(mask='dongs!cocks@lol.org'))
    'Hostmask(dongs!cocks@lol.org)'
    >>> repr(Hostmask.parse(mask='dongs@lol.org'))
    'Hostmask(dongs@lol.org)'
    >>> repr(Hostmask.parse(mask='lol.org'))
    'Hostmask(lol.org)'
    """

    __slots__ = ('nick', 'username', 'host', 'maskstr')

    def __init__(self, *, nick=None, username=None, host=None, mask=None):
        """Initalise the Hostmask object"""
        self.nick = nick
        self.username = username
        self.host = host
        self.maskstr = mask

    @classmethod
    def parse(cls, raw):
        """Parse a raw hostmask into a Hostmask object.

        Arguments:

        raw
            The raw hostmask to parse.
        """

        if not raw:
            logger.debug("No hostmask found")
            return

        host_sep = raw.find('@')
        if host_sep == -1:
            if(raw.find('.') != -1):
                return cls(host=raw, mask=raw)
            else:
                return cls(nick=raw, mask=raw)

        nick_sep = raw.find('!')
        has_username = (nick_sep != -1)
        if not has_username:
            return cls(nick=raw[:host_sep], host=raw[host_sep + 1:],
                       mask=raw)
        else:
            return cls(nick=raw[:nick_sep],
                       username=raw[nick_sep + 1:host_sep],
                       host=raw[host_sep + 1:], mask=raw)

    def __str__(self):
        if not self.maskstr:
            if not any((self.nick, self.username, self.host)):
                self.maskstr = ''

            if self.nick and not self.host:
                # Nick only
                self.maskstr = self.nick

            elif not self.nick and self.host:
                # Host only
                self.maskstr = self.host
            else:
                # Both
                if self.username:
                    self.maskstr = '{}!{}@{}'.format(self.nick, self.username,
                                                     self.host)
                else:
                    self.maskstr = '{}@{}'.format(self.nick, self.host)

        return self.maskstr

    def __bytes__(self):
        return str(self).encode('utf-8', 'replace')

    def __repr__(self):
        return 'Hostmask({})'.format(str(self))


class Line:
    """ Stores an IRC line

    This uses RFC1459 framing.

    >>> repr(Line.parse(':lol.org PRIVMSG'))
    'Line(:lol.org PRIVMSG)'
    >>> repr(Line.parse('PING'))
    'Line(PING)'
    >>> repr(Line.parse('PING Elizacat'))
    'Line(PING Elizacat)'
    >>> repr(Line.parse('PING Elizacat :dongs'))
    'Line(PING Elizacat :dongs)'
    >>> repr(Line.parse('PING :dongs'))
    'Line(PING :dongs)'
    >>> repr(Line.parse(':dongs!dongs@lol.org PRIVMSG loldongs meow :dongs'))
    'Line(:dongs!dongs@lol.org PRIVMSG loldongs meow :dongs)'
    """

    __slots__ = ('tags', 'hostmask', 'command', 'params', 'linestr')

    IN = True
    OUT = False

    def __init__(self, *, tags=None, hostmask=None, command=None, params=None,
                 line=None):
        """Initalise the Line object."""

        self.tags = tags
        self.hostmask = hostmask
        self.command = command
        self.params = params if params is not None else list()
        self.linestr = line

        if isinstance(self.tags, str):
            self.tags = Tags.parse(self.tags)

        if isinstance(self.hostmask, str):
            self.hostmask = Hostmask.parse(self.hostmask)

        if isinstance(self.command, int):
            self.command = str(self.command)

    """ Parse an IRC line.

    100% regex free, thanks to a certain fox.

    Also should raise on any invalid line.  It will be quite liberal with
    hostmasks (accepting such joys as '' and 'user1@user2@user3'), but trying
    to enforce strict validity in hostmasks will be slow. """
    @classmethod
    def parse(cls, line):
        if not line:
            logger.warning("Blank line passed in!")
            return

        raw_line = line
        tags = None
        hostmask = None
        params = list()

        # Do we have tags?
        if line[0] == '@':
            space = line.index(' ')  # Grab the separator
            tags = Tags.parse(line[1:space])
            line = line[space:].lstrip()

        # Do we have a hostmask?
        if line[0] == ':':
            space = line.index(' ')  # Grab the separator
            hostmask = Hostmask.parse(line[1:space])
            line = line[space:].lstrip()

        # Grab command
        command = reduce(operator.concat,
                         takewhile(lambda char: char not in (' ', ':'), line))
        assert len(command) > 0

        line = line[len(command):].lstrip().rstrip('\r\n')

        # Retrieve parameters
        while len(line) > 0:
            next_param = ''
            line = line.lstrip()

            if not line:
                # XXX is this really the correct behaviour?
                next_param = ''
                break

            if line[0] == ':':
                next_param = line[1:]
                line = ''
            else:
                next_param = reduce(operator.concat,
                                    takewhile(lambda char: char != ' ', line))
                line = line[len(next_param):]

            params.append(next_param)

        return cls(tags=tags, hostmask=hostmask, command=command,
                   params=params, line=raw_line)

    def __str__(self):
        if not self.linestr:
            line = []
            if self.hostmask:
                line.append(':' + str(self.hostmask))

            line.append(self.command)

            if self.params:
                if any(x in (' ', ':') for x in self.params[-1]):
                    line.extend(self.params[:-1])
                    line.append(':' + self.params[-1])
                else:
                    line.extend(self.params)

            self.linestr = ' '.join([str(x) for x in line]) + '\r\n'

        return self.linestr

    def __bytes__(self):
        return str(self).encode('utf-8', 'replace')

    def __repr__(self):
        return 'Line({})'.format(str(self).rstrip('\r\n'))

    def __hash__(self):
        return hash(str(self))

if __name__ == '__main__':
    import doctest
    doctest.testmod()
