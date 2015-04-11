# Copyright © 2013-2015 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


""" Parsing for various IRC mini-languages.

IRC has a mini-language/grammar fetish and uses them extensively to compensate
for the fact that RFC1459 frames are deficient, to be excessively generous.

This module has various parsers for some of them (by no means exhaustive - and
that's probably not even possible, given everyone and their dog seems to love
inventing new ones for no discernible reason).

Hopefully one day this module will disappear, when IRC gets a sane framing
format. Until that day comes, this needs to be here.
"""


from collections import defaultdict
from re import compile
from string import ascii_letters, digits
from types import SimpleNamespace
from logging import getLogger

from PyIRC.line import Line


logger = getLogger(__name__)


prefix_match = compile(r"\(([A-Za-z0-9]+)\)(.+)")
numletters = ascii_letters + digits


def prefix_parse(prefix):
    """ Parse ISUPPORT prefix """

    match = prefix_match.match(prefix)
    if not match:
        return {}

    return {k : v for k, v in zip(*match.groups())}


def mode_parse(modes, params, modegroups):
    """ Parse IRC mode strings """

    adding = True
    for c in modes:
        if c == '+':
            adding = True
            continue
        elif c == '-':
            adding = False
            continue

        param = None
        if adding:
            if c in modegroups[0] + modegroups[1] + modegroups[2]:
                param = params.pop(0)
        else:
            if c in modegroups[0] + modegroups[2]:
                param = params.pop(0)

        yield (c, param, adding)


def who_flag_parse(flags):
    """ Parse WHO flags """

    ret = SimpleNamespace()
    ret.operator = False
    ret.away = False
    ret.modes = set()

    for char in flags:
        if char == '*':
            ret.operator = True
        elif char == "G":
            ret.away = True
        elif char == "H":
            ret.away = False
        elif char not in numletters:
            ret.modes.add(char)
        else:
            logger.debug("No known way to handle WHO flag %s", char)

    return ret


def isupport_parse(params):
    """ Parse an ISUPPORT string """

    supported = dict()

    for param in params:
        # Split into key : value pair
        key, _, value = param.partition('=')

        if not value:
            logger.debug("ISUPPORT [k]: %s", key)
            supported[key] = True
            continue

        # Parse into CSV
        value = value.split(',')

        # For each value, parse into pairs of val : data
        for i, v in enumerate(value):
            val, sep, data = v.partition(':')
            if sep:
                if not data:
                    data = None

                value[i] = (val, data)

        if len(value) == 1:
            # Single key
            value = value[0]

        logger.debug("ISUPPORT [k:v]: %s:%r", key, value)
        supported[key] = value

    return supported


class CTCPMessage:
    """ Represent a CTCP message. """

    __slots__ = ('msgtype', 'command', 'target', 'param')

    def __init__(self, type, command, target, param):
        self.msgtype = type
        self.command = command
        self.target = target
        self.param = param

    @classmethod
    def parse(cls, line):
        """ Return a new CTCPMessage from the line specified. """

        message = line.params[1]

        if not message.startswith("\x01") or not message.endswith("\x01"):
            return None

        message = message[1:-1]  # chop off \x01 at beginning and end
        (command, _, param) = message.partition(' ')

        return cls(line.command.upper(), command.upper(), line.hostmask.nick,
                   param)

    def line(self):
        """ Return a Line instance representing this CTCP message """

        str = '\x01{} {}\x01'.format(self.command, self.param)
        return Line(command=self.msgtype, params=[self.target, str])
