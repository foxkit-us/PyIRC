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


from functools import lru_cache
from re import compile
from string import ascii_letters, digits
from types import SimpleNamespace
from logging import getLogger

from PyIRC.line import Line


logger = getLogger(__name__)


prefix_match = compile(r"\(([A-Za-z0-9]+)\)(.+)")
numletters = ascii_letters + digits


@lru_cache
def prefix_parse(prefix):
    """ Parse ISUPPORT PREFIX extension into mode : prefix and vice versa.

    Arguments:

    prefix
        String from ISupport.supported['PREFIX']

    .. warning:

    >>> sorted(prefix_parse("(ov)@+").items())
    [('+', 'v'), ('@', 'o'), ('o', '@'), ('v', '+')]
    >>> sorted(prefix_parse("(qahov)~&%@+").items())[:5]
    [('%', 'h'), ('&', 'a'), ('+', 'v'), ('@', 'o'), ('a', '&')]
    >>> prefix_parse("(ov)@+")["@"]
    'o'
    >>> prefix_parse("(ov)@+")["o"]
    '@'
    >>> prefix_parse("(o)@+")
    Traceback (most recent call last):
        ...
    ValueError: Unbalanced modes and prefixes
    """

    ret = dict()

    match = prefix_match.match(prefix)
    if not match:
        return ret

    modes, values = match.groups()
    if len(modes) != len(values):
        raise ValueError("Unbalanced modes and prefixes")

    for k, v in zip(modes, values):
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

    >>> modegroups = ("beIq", "k", "flj", "ac")
    >>> prefixmodes = "(ov)@+"
    >>> f = lambda x: [(char, param, adding) for char, param, adding in x]
    >>> f(mode_parse("+oba", ("a", "b"), modegroups, prefixmodes))
    [('o', 'a', True), ('b', 'b', True), ('a', None, True)]
    >>> f(mode_parse("+o-o", ("a", "a"), modegroups, prefixmodes))
    [('o', 'a', True), ('o', 'a', False)]
    >>> f(mode_parse("+k-k", ("test",), modegroups, prefixmodes))
    [('k', 'test', True), ('k', None, False)]
    >>> f(mode_parse("+bf-k+b", ("a", "b", "c"), modegroups, prefixmodes))
    [('b', 'a', True), ('f', 'b', True), ('k', None, False), ('b', 'c', True)]
    >>> prefixmodes = prefix_parse(prefixmodes)
    >>> f(mode_parse("+ov-v", ("a", "b", "c"), modegroups, prefixmodes))
    [('o', 'a', True), ('v', 'b', True), ('v', 'c', False)]
    """
    if not hasattr(prefix, 'items'):
        prefix = prefix_parse(prefix)

    params = list(params)

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


@lru_cache
def status_prefix_parse(string, prefix):
    """ Parse a string containing status sigils

    Returns a simple (string, status) tuple

    Arguments:

    string
        Nick or channel containing leading sigils.

    prefix
        The mode prefixes from ISupport.supported['PREFIX'], optionally parsed
        by prefix_parse

    >>> status_prefix_parse("@#channel", "(ov)@+")
    ({'@'}, '#channel')
    >>> status_prefix_parse("+#ch@nnel", "(ov)@+")
    ({'+'}, '#ch@nnel')
    >>> status_prefix_parse("+#", "(ov)@+")
    ({'+'}, '#')
    >>> modes, channel = status_prefix_parse("@+#", "(ov)@+")
    >>> sorted(modes), channel
    (['+', '@'], '#')
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


@lru_cache
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


@lru_cache
def isupport_parse(params):
    """ Parse an ISUPPORT string

    Returns a parsed dictionary of all ISUPPORT items from the parameter list

    Arguments:

    params
        Params to parse into ISUPPORT entries in the dictionary

    >>> isupport_parse(["CHANTYPES=a,b,cdefg"])
    {'CHANTYPES': ['a', 'b', 'cdefg']}
    >>> isupport_parse(["EXCEPTS"])
    {'EXCEPTS': True}
    >>> isupport_parse(["PREFIX=(ov)@+"])
    {'PREFIX': '(ov)@+'}
    >>> isupport_parse(["MAXLIST=ACCEPT:5"])
    {'MAXLIST': ('ACCEPT', '5')}
    >>> isupport_parse(["MAXLIST=ACCEPT:,TEST:5"])
    {'MAXLIST': [('ACCEPT', None), ('TEST', '5')]}
    >>> sorted((k, v) for k, v in isupport_parse(["EXCEPTS", "INVEX"]).items())
    [('EXCEPTS', True), ('INVEX', True)]
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
        value = list(filter(None, value.split(',')))

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
    r"""Represent a CTCP message.

    >>> CTCPMessage("PRIVMSG", "PING", "#Sporks", "lol")
    ... # doctest: +ELLIPSIS
    CTCPMessage(...='PRIVMSG', ...='PING', ...='#Sporks', ...='lol')
    >>> CTCPMessage("PRIVMSG", "PING", "#Sporks", "lol").line
    ... # doctest: +ELLIPSIS
    Line(..., command='PRIVMSG', params=['#Sporks', '\x01PING lol\x01'])
    >>> line = Line(tags=None, hostmask=None, command='PRIVMSG',
    ... params=['#test', '\x01TEST TEST\x01'])
    >>> CTCPMessage.parse(line)
    ... # doctest: +ELLIPSIS
    CTCPMessage(msgtype='PRIVMSG', ...='TEST', ...='#test', param='TEST')
    """

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
        """Return a new :py:class::`CTCPMessage` from the line specified

        Arguments:

        line
            A Line instance to parse into a :py:class::`CTCPMessage`
        """
        message = line.params[1]

        if not message.startswith("\x01") or not message.endswith("\x01"):
            return None

        message = message[1:-1]  # chop off \x01 at beginning and end
        (command, _, param) = message.partition(' ')
        param = param.strip()
        if not param:
            param = None

        if not line.hostmask or not line.hostmask.nick:
            target = line.params[0]
        else:
            target = line.hostmask.nick

        return cls(line.command.upper(), command.upper(), target, param)

    @property
    def line(self):
        """Return a :py:class::`Line` instance representing this CTCP message"""
        message = '\x01{} {}\x01'.format(self.command, self.param)
        return Line(command=self.msgtype, params=[self.target, message])

    def __repr__(self):
        return "CTCPMessage(msgtype={}, command={}, target={}, " \
            "param={})".format(repr(self.msgtype), repr(self.command),
                              repr(self.target), repr(self.param))
