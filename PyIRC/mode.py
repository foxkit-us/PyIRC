# Copyright © 2013-2015 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


""" Basic modes parser """


from collections import defaultdict
from re import compile
from string import ascii_letters, digits
from types import SimpleNamespace
from logging import getLogger


logger = getLogger(__name__)


prefix_match = compile(r"\(([A-Za-z0-9]+)\)(.+)")
numletters = ascii_letters + digits

def prefix_parse(prefix):
    """ Parse ISUPPORT prefix """

    match = prefix_match.match(prefix)
    if not match:
        return {}

    return {k : v for k, v in zip(*match.groups())}


def mode_parse(modes, params):
    """ Parse IRC modes using the IRC state machine """

    # Return value (user : modes}
    mode_add = defaultdict(set)
    mode_del = defaultdict(set)

    op = mode_add
    for c in modes:
        if c == '+':
            op = mode_add
            continue
        elif c == '-':
            op = mode_del
            continue

        op[params.pop(0)].add(c)

    return (mode_add, mode_del)

def who_flag_parse(flags):
    """ Parse WHO flags """

    ret = SimpleNamespace()
    ret.operator = False
    ret.away = false
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
