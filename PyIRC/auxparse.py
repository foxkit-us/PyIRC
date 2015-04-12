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
    """ Parse ISUPPORT PREFIX extension into mode : prefix and vice versa.

    Arguments:

    prefix
        String from ISupport.supported['PREFIX']
    """

    ret = dict()

    match = prefix_match.match(prefix)
    if not match:
        return ret

    for k, v in zip(*match.groups()):
        ret[k] = v
        ret[v] = k
    return ret


def mode_parse(modes, params, modegroups, prefix):
    """ Parse IRC mode strings

    A generator that yields (modechar, param, adding). param may be None.
    adding will either be True or False, depending on what is happening to the
    mode.

    Arguments:

    modes
        Initial string of modes (should resemble +blah/-blah or some such)

    params
        Parameters for the modes, likely the remaining parameters after modes

    modegroups
        The item from ISupport.supported['CHANMODES']

    prefix
        The mode prefixes from ISupport.supported['PREFIX'], optionally parsed
        by prefix_parse
    """
    if not hasattr(prefix, 'items'):
        prefix = prefix_parse(prefix)

    status = ''.join(mode for mode in prefix if mode in ascii_letters)

    # Groups of modes
    group_pop_add = modegroups[0] + modegroups[1] + modegroups[2] + status
    group_pop_remove = modegroups[0] + modegroups[2] + status

    adding = True
    group = group_pop_add
    for char in modes:
        if char == '+':
            adding = True
            group = group_pop_add
            continue
        elif char == '-':
            adding = False
            group = group_pop_remove
            continue

        param = None
        if char in group:
            param = params.pop(0)

        yield (char, param, adding)


def status_prefix_parse(string, prefix):
    """ Parse a string containing status sigils

    Returns a simple (string, status) tuple

    Arguments:

    nick
        Nick containing leading sigils.

    prefix
        The mode prefixes from ISupport.supported['PREFIX'], optionally parsed
        by prefix_parse
    """
    if not hasattr(prefix, 'items'):
        prefix = prefix_parse(prefix)

    modes = set()
    for char in str(string):
        if string[0] in prefix:
            prefix_char, string = string[0], string[1:]
            modes.add(prefix_char)
        else:
            return (modes, string)


def who_flag_parse(flags):
    """ Parse WHO flags

    Returns a namespace object containing the following attributes:

    operator
        Whether or not the user is an operator

    away
        Whether or not the user is away

    modes
        A set of the user's present modes (prefixes)

    Arguments:

    flags
        Flags to parse
    """
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
    """ Parse an ISUPPORT string

    Returns a parsed dictionary of all ISUPPORT items from the parameter list

    Arguments:

    params
        Params to parse into ISUPPORT entries in the dictionary
    """
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

    def __init__(self, msgtype, command, target, param):
        """Initalise the CTCPMessage instance

        Arguments:

        msgtype
            The type of message received, either PRIVMSG or NOTICE
        
        command
            The CTCP command used (e.g., PING, TIME, VERSION)

        target
            The target of this given CTCP request or response

        param
            The param(s) of the CTCP message, with no parsing attempted.
        """
        self.msgtype = msgtype
        self.command = command
        self.target = target
        self.param = param

    @classmethod
    def parse(cls, line):
        """Return a new `CTCPMessage` from the line specified

        Arguments:

        line
            A Line instance to parse into a CTCPMessage
        """
        message = line.params[1]

        if not message.startswith("\x01") or not message.endswith("\x01"):
            return None

        message = message[1:-1]  # chop off \x01 at beginning and end
        (command, _, param) = message.partition(' ')

        return cls(line.command.upper(), command.upper(), line.hostmask.nick,
                   param)

    def line(self):
        """Return a ``Line`` instance representing this CTCP message"""
        str = '\x01{} {}\x01'.format(self.command, self.param)
        return Line(command=self.msgtype, params=[self.target, str])
