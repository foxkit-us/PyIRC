# Copyright © 2013-2015 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


r""" IRC-style casemapping and casefolding

IRC uses two forms of casemapping: RFC1459 and ASCII. Unicode is not handled
or casemapped by any known servers.

ASCII is simply casemapped as "abc..." <-> "ABC...".

RFC1459 is the same as ASCII in terms of casefolding semantics, except that
the characters {}|- are the lowercase equivalents of []\^. This is due to an
historical wart in the protocol.
"""


from string import ascii_lowercase, ascii_uppercase
from collections import UserString, UserDict
from collections.abc import MutableSet


# Translation tables
# NB - IRC is only ASCII-aware, not unicode-aware!
rfc1459_lower = ascii_lowercase + "{}|~"   # I don't make the rules,
rfc1459_upper = ascii_uppercase + "[]\\^"  # I just enforce them.

rfc1459_tolower = str.maketrans(rfc1459_upper, rfc1459_lower)
rfc1459_toupper = str.maketrans(rfc1459_lower, rfc1459_upper)

ascii_tolower = str.maketrans(ascii_uppercase, ascii_lowercase)
ascii_toupper = str.maketrans(ascii_lowercase, ascii_uppercase)


class IRCString(UserString):

    r"""An IRC string.

    Same as a normal string, with IRC style casemapping.

    >>> s = IRCString('Søs', IRCString.ASCII)
    >>> s
    'Søs'
    >>> s.irc_upper()
    'SøS'
    >>> s.irc_lower()
    'søs'
    >>> s.irc_casefold()
    'søs'
    >>> s = IRCString('Têst{}|~', IRCString.RFC1459)
    >>> s
    'Têst{}|~'
    >>> s.irc_lower()
    'têst{}|~'
    >>> s.irc_upper()
    'TêST[]\\^'
    """

    UNICODE = 0
    ASCII = 1
    RFC1459 = 2

    def __init__(self, case, string):
        """Create a new IRC String.

        Arguments:

        :param case:
            Casemapping, can be UNICODE, ASCII, or RFC1459. This controls the
            behaviour of the irc_* functions.

        :param string:
            String to use
        """
        self.case = case
        super().__init__(string)

    def upper(self):
        """Uppercase string according to default semantics"""
        if self.case == IRCString.ASCII:
            return self.ascii_upper()
        elif self.case == IRCString.RFC1459:
            return self.rfc1459_upper()
        else:
            return str.upper(self.data)

    def lower(self):
        """Lowercase string according to default semantics"""
        if self.case == IRCString.ASCII:
            return self.ascii_lower()
        elif self.case == IRCString.RFC1459:
            return self.rfc1459_lower()
        else:
            return str.lower(self.data)

    def casefold(self):
        """Casefold string according to default semantics"""
        if self.case == IRCString.ASCII:
            return self.ascii_casefold()
        elif self.case == IRCString.RFC1459:
            return self.rfc1459_casefold()
        else:
            return str.casefold(self.data)

    def __hash__(self):
        return hash(self.casefold())

    def __gt__(self, other):
        if not hasattr(other, 'case'):
            other = IRCString(self.case, other)
        elif other.case != self.case:
            other = other.convert(self.case)

        return self.casefold() > other.casefold()

    def __lt__(self, other):
        if not hasattr(other, 'case'):
            other = IRCString(self.case, other)
        elif other.case != self.case:
            other = other.convert(self.case)

        return self.casefold() < other.casefold()

    def __eq__(self, other):
        if not hasattr(other, 'case'):
            other = IRCString(self.case, other)
        elif other.case != self.case:
            other = other.convert(self.case)

        return self.casefold() == other.casefold()

    def __ne__(self, other):
        if not hasattr(other, 'case'):
            other = IRCString(self.case, other)
        elif other.case != self.case:
            other = other.convert(self.case)

        return self.casefold() != other.casefold()

    def __ge__(self, other):
        if not hasattr(other, 'case'):
            other = IRCString(self.case, other)
        elif other.case != self.case:
            other = other.convert(self.case)

        return self.casefold() >= other.casefold()

    def __le__(self, other):
        if not hasattr(other, 'case'):
            other = IRCString(self.case, other)
        elif other.case != self.case:
            other = other.convert(self.case)

        return self.casefold() <= other.casefold()

    def convert(self, case):
        """Convert string into another caseform"""
        return IRCString(self, case)

    def ascii_lower(self):
        """Return a copy of the string S converted to lowercase, using ASCII
        semantics."""
        return str.translate(self.data, ascii_tolower)

    def ascii_upper(self):
        """Return a copy of the string S converted to uppercase, using ASCII
        semantics."""
        return str.translate(self.data, ascii_toupper)

    def ascii_casefold(self):
        """Return a version of S suitable for caseless comparisons, using
        ASCII semantics."""
        return str.translate(self.data, ascii_tolower)

    def rfc1459_lower(self):
        """Return a copy of the string S converted to lowercase, using RFC1459
        semantics."""
        return str.translate(self.data, rfc1459_tolower)

    def rfc1459_upper(self):
        """Return a copy of the string S converted to uppercase, using RFC1459
        semantics."""
        return str.translate(self.data, rfc1459_toupper)

    def rfc1459_casefold(self):
        """Return a version of S suitable for caseless comparisons, using
        RFC1459 semantics."""
        return str.translate(self.data, rfc1459_tolower)

    def __repr__(self):
        return "IRCString({})".format(super().__repr__())


class IRCDict(UserDict):

    """An IRC dictionary class, with caseless key lookup"""

    def __init__(self, case, *args, **kwargs):
        self.case = case
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        if isinstance(key, str):
            key = IRCString(self.case, key)
        elif hasattr(key, 'convert'):
            key = IRCString(key.convert(self.case), self.case)

        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if isinstance(key, str):
            key = IRCString(self.case, key)
        elif hasattr(key, 'convert'):
            key = IRCString(key.convert(self.case), self.case)

        return super().__setitem__(key, value)

    def __delitem__(self, key):
        if isinstance(key, str):
            key = IRCString(self.case, key)
        elif hasattr(key, 'convert'):
            key = IRCString(key.convert(self.case), self.case)

        return super().__delitem__(key)

    def __contains__(self, key):
        if isinstance(key, str):
            key = IRCString(self.case, key)
        elif hasattr(key, 'convert'):
            key = IRCString(key.convert(self.case), self.case)

        return super().__contains__(key)

    def convert(self, case):
        """Convert dictionary to new casemapping"""
        new = IRCDict(case)
        for key, value in self.items():
            if isinstance(key, str):
                key = IRCString(self.case, key)
            elif hasattr(key, 'convert'):
                key = IRCString(key.convert(self.case), self.case)

            new[key] = value

        return new

    def __repr__(self):
        return "IRCDict({}, {})".format(self.case, super().__repr__())


class IRCDefaultDict(IRCDict):

    """Similar to the built in :py:class:`defaultdict`, but with the semantics
    of :py:class:`~PyIRC.casemapping.IRCDict`."""

    def __init__(self, case, default, *args, **kwargs):
        self.default = default
        super().__init__(case, *args, **kwargs)

    def __missing__(self, key):
        if isinstance(key, str):
            key = IRCString(self.case, key)
        elif hasattr(key, 'convert'):
            key = IRCString(key.convert(self.case), self.case)

        return self.default()

    def __repr__(self):
        return "IRCDefaultDict({}, {}, {})".format(self.case, self.default,
                                                   UserDict.__repr__(self))


class IRCSet(MutableSet):

    """An IRC set class, with caseless members"""

    def __init__(self, case, iterable=set()):
        self.case = case
        self.store = set()
        for item in iterable:
            self.add(item)

    def add(self, item):
        if isinstance(item, str):
            item = IRCString(self.case, item)
        elif hasattr(item, 'convert'):
            item = IRCString(item.convert(self.case), self.case)

        self.store.add(item)

    def discard(self, item):
        if isinstance(item, str):
            item = IRCString(self.case, item)
        elif hasattr(item, 'convert'):
            item = IRCString(item.convert(self.case), self.case)

        self.store.discard(item)

    def convert(self, case):
        new = IRCSet(case)
        for item in self:
            if isinstance(item, str):
                item = IRCString(self.case, item)
            elif hasattr(item, 'convert'):
                item = item.convert(case)

            new.add(item)

        return new

    def __contains__(self, item):
        if isinstance(item, str):
            item = IRCString(self.case, item)
        elif hasattr(item, 'convert'):
            item = IRCString(item.convert(self.case), self.case)

        return item in self.store

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __repr__(self):
        return "IRCSet({}, {})".format(self.case, super().__repr__())
