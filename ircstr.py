# Copyright © 2013-2015 Elizabeth Myers and Andrew Wilcox.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.

""" Basic IRC strings. This is important, as channels/users are case-agnostic
and usually follow wonky RFC1459 semantics. The only time this is not true is
on IRCNet. """

from collections import UserString
import re

_upper = "[]\\"
_lower = "{}|"
_re_upper = r"\[\]\\"
_re_lower = r"\{\}\|"

# Translation stuff
_ttable_upper = str.maketrans(_lower, _upper)
_ttable_lower = str.maketrans(_upper, _lower)
trans_upper = lambda text : text.translate(_ttable_upper)
trans_lower = lambda text : text.translate(_ttable_lower)

# Is upper/lower
_isupper = re.compile("[{_re_upper}]".format(**locals()))
_islower = re.compile("[{_re_lower}]".format(**locals()))

class BaseStr(UserString):
    """ Base string class. Implements a case-agnostic string. """

    __slots__ = ('data', 'ldata')

    def __init__(self, seq):
        UserString.__init__(self, seq)
        self.ldata = self.casefold()

    def casefold(self):
        return self.data.casefold()

    def upper(self):
        return self.data.upper()

    def lower(self):
        return self.data.lower()

    def __eq__(self, string):
        if isinstance(string, BaseStr):
            string = string.ldata
        elif isinstance(string, UserString):
            string = string.data
        else:
            string = string.casefold()

        return str.__eq__(self.ldata, string)

    def __ne__(self, string):
        if isinstance(string, BaseStr):
            string = string.ldata
        elif isinstance(string, UserString):
            string = string.data
        else:
            string = string.casefold()

        return str.__ne__(self.ldata, string)

    def __gt__(self, string):
        if isinstance(string, BaseStr):
            string = string.ldata
        elif isinstance(string, UserString):
            string = string.data
        else:
            string = string.casefold()

        return str.__gt__(self.ldata, string)

    def __lt__(self, string):
        if isinstance(string, BaseStr):
            string = string.ldata
        elif isinstance(string, UserString):
            string = string.data
        else:
            string = string.casefold()

        return str.__lt__(self.ldata, string)

    def __le__(self, string):
        if isinstance(string, BaseStr):
            string = string.ldata
        elif isinstance(string, UserString):
            string = string.data
        else:
            string = string.casefold()

        return str.__le__(self.ldata, string)

    def __ge__(self, string):
        if isinstance(string, BaseStr):
            string = string.ldata
        elif isinstance(string, UserString):
            string = string.data
        else:
            string = string.casefold()

        return str.__ge__(self.ldata, string)

    def __hash__(self): return hash(self.ldata)

    def raw_compare(self, string):
        return str.__eq__(self, string)

class ASCIIStr(BaseStr):
    """ Simple derivative of BaseStr. """
    __slots__ = ('data', 'ldata')
    pass

class RFC1459Str(BaseStr):
    """ Derivative of BaseStr that implements RFC1459 case mapping semantics.

    This will be used for channels, idents, and nicknames.
    """
    __slots__ = ('data', 'ldata')

    def casefold(self):
        return trans_lower(BaseStr.casefold(self))

    def upper(self):
        return trans_upper(BaseStr.upper(self))

    def lower(self):
        return trans_lower(BaseStr.lower(self))

    def isupper(self):
        return BaseStr.isupper(self) and not _islower.match(self)

    def islower(self):
        return BaseStr.islower(self) and not _isupper.match(self)

    def capitalize(self):
        s = BaseStr.capitalize(self)
        if _islower.match(s[0]):
            s = trans_upper(s[0]) + s[1:]

        return s

    def swapcase(self):
        s = []
        for ch in BaseStr.swapcase(self):
            if _islower.match(ch):
                ch = trans_upper(ch)
            elif __isupper.match(ch):
                ch = trans_lower(ch)

            ch.append(s)

        return ''.join(s)


