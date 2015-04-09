# Copyright © 2013-2015 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


""" IRC casefoldping """


from string import ascii_lowercase, ascii_uppercase


# Translation tables
# NB - IRC is only ASCII-aware, not unicode-aware!
rfc1459_lower = ascii_lowercase + "{}|~"  # I don't make the rules,
rfc1459_upper = ascii_uppercase + "[]\\^" # I just enforce them. 

rfc1459_tolower = str.maketrans(rfc1459_upper, rfc1459_lower)
rfc1459_toupper = str.maketrans(rfc1459_lower, rfc1459_upper)

ascii_tolower = str.maketrans(ascii_lowercase, ascii_uppercase)
ascii_toupper = str.maketrans(ascii_uppercase, ascii_lowercase)


class IRCString(str):
    """ An IRC string """

    UNICODE = 0
    ASCII = 1
    RFC1459 = 2

    def __new__(cls, s, case):
        self = super(IRCString, cls).__new__(cls, s)

        if case == IRCString.ASCII:
            self.irc_lower = self.ascii_lower
            self.irc_upper = self.ascii_upper
            self.irc_casefold = self.ascii_casefold
        elif case == IRCString.RFC1459:
            self.irc_lower = self.rfc1459_lower
            self.irc_upper = self.rfc1459_upper
            self.irc_casefold = self.rfc1459_casefold
        else:
            # yay unicode
            self.irc_lower = self.lower
            self.irc_upper = self.upper
            self.irc_casefold = self.casefold

        return self

    def ascii_lower(self):
        return str.translate(self, ascii_tolower)

    def ascii_upper(self):
        return str.translate(self, ascii_toupper)

    def ascii_casefold(self):
        return str.translate(self, ascii_tolower)

    def rfc1459_lower(self):
        return str.translate(self, rfc1459_tolower)

    def rfc1459_upper(self):
        return str.translate(self, rfc1459_toupper)

    def rfc1459_casefold(self):
        return str.translate(self, rfc1459_tolower)

