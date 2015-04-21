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

    Not presently tested a whole lot due to the lack of conforming
    servers.
    """

    __slots__ = ('tags', 'tagstr')

    def __init__(self, *, tags=None, tagstr=None):
        self.tags = tags
        self.tagstr = tagstr

        if not self.tags:
            self = self.parse(self.tagstr)

    @classmethod
    def parse(cls, raw):
        """Parse a raw tag string into a Tags object."""
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

    def __repr__(self):
        return "Tags(tags={})".format(repr(self.tags))

    def __str__(self):
        ret = []
        for key, value in self.tags.items():
            if value is None:
                value = ''

            ret.append('{}={}'.format(key, value))

        return ';'.join(ret)


class Hostmask:

    """ Stores a hostmask

    Hostmasks are used to store sources and destinations in IRC messages.

    >>> Hostmask.parse('nick!user@host')
    Hostmask(nick='nick', username='user', host='host')
    >>> Hostmask.parse('nick@host')
    Hostmask(nick='nick', username=None, host='host')
    >>> Hostmask.parse('host.org')
    Hostmask(nick=None, username=None, host='host.org')
    >>> Hostmask.parse('nickname')
    Hostmask(nick='nickname', username=None, host=None)
    """

    __slots__ = ('nick', 'username', 'host', 'maskstr')

    def __init__(self, *, nick=None, username=None, host=None, mask=None):
        """Initalise the Hostmask object"""
        self.nick = nick
        self.username = username
        self.host = host
        self.maskstr = mask

        if not self.maskstr:
            str(self)

    @classmethod
    def parse(cls, raw):
        """Parse a raw hostmask into a Hostmask object.

        :param raw:
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
        return "Hostmask(nick={}, username={}, host={})".format(
            repr(self.nick), repr(self.username), repr(self.host))


class Line:

    """Stores an IRC line in the RFC1459 framing format.

    IRCv3 has a JSON framing format in the works, but it is unclear as to what
    its final server and client support will be, and is unfinished at any
    rate.

    >>> Line.parse(':lol.org PRIVMSG')
    ... # doctest: +ELLIPSIS
    Line(..., hostmask=Hostmask(...), command='PRIVMSG', params=[])
    >>> Line.parse('PING')
    Line(tags=None, hostmask=None, command='PING', params=[])
    >>> Line.parse('PING Elizacat')
    Line(tags=None, hostmask=None, command='PING', params=['Elizacat'])
    >>> Line.parse('PING Elizacat :test')
    Line(tags=None, hostmask=None, command='PING', params=['Elizacat', 'test'])
    >>> Line.parse('PING :test')
    Line(tags=None, hostmask=None, command='PING', params=['test'])
    >>> Line.parse(':nick!user@host PRIVMSG #testroom meow :testing')
    ... # doctest: +ELLIPSIS
    Line(..., command='PRIVMSG', params=['#testroom', 'meow', 'testing'])
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

        if self.linestr is None:
            str(self)

    @classmethod
    def parse(cls, line):
        """Parse a raw string into a Line.

        Also should raise on any invalid line.  It will be quite liberal with
        hostmasks (accepting such joys as '' and 'user1@user2@user3'), but
        trying to enforce strict validity in hostmasks will be slow.
        """
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
        return "Line(tags={}, hostmask={}, command={}, params={})".format(
            repr(self.tags), repr(self.hostmask), repr(self.command),
            repr(self.params))

    def __hash__(self):
        return hash(str(self))
