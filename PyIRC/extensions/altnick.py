# Copyright © 2015-2019 A. Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Some alternate nick handlers.

This contains an underscore-appending handler and a number-substituting
(leetifying) handler.
"""


from logging import getLogger
from abc import ABCMeta, abstractmethod

from PyIRC.signal import event
from PyIRC.numerics import Numerics
from PyIRC.extensions import BaseExtension


_logger = getLogger(__name__)  # pylint: disable=invalid-name


class BaseAlt(BaseExtension, metaclass=ABCMeta):
    """Base class inherited for altnick extensions.

    This provides a basic framework for all alt nickname classes to use.

    This class does nothing on its own, you want either
    :py:class:`~PyIRC.extensions.UnderscoreAlt`,
    :py:class:`~PyIRC.extensions.NumberSubstituteAlt`, or a custom
    implementation (that should inherit from this class!).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.attempt_nick = self.nick  # From base
        self.exhausted = False  # Whether or not to throw in the towel
        self.our_turn = False

    def check_our_turn(self):
        if self.our_turn:
            return True

        for extension in self.get_extension_subclasses(BaseAlt):
            if not extension.exhausted:
                return False

            if extension == self:
                self.our_turn = True
                return True

        _logger.critical("BUG: Got somewhere we shouldn't have!")
        raise AssertionError()

    @abstractmethod
    def try_nick(self):
        """Return a nickname to try."""
        raise NotImplementedError

    @event("commands", Numerics.ERR_NICKNAMEINUSE, priority=-1000)
    @event("commands", Numerics.ERR_ERRONEOUSNICKNAME, priority=-1000)
    @event("commands", Numerics.ERR_NONICKNAMEGIVEN, priority=-1000)
    def change_nick(self, _, line):
        """Try to change our nickname to an alternative."""
        if self.registered:
            return

        if self.exhausted or not self.check_our_turn():
            return

        try:
            self.attempt_nick = self.try_nick()
        except ValueError:
            _logger.debug("altnick: module %s exhausted",
                          self.__class__.__name__)
            self.exhausted = True
            return

        self.send("NICK", [self.attempt_nick])


class UnderscoreAlt(BaseAlt):
    """This class attempts to append underscores to the nickname.

    If :py:class:`~PyIRC.extensions.ISupport` is present, it will try
    until the maximum nick length is reached; otherwise, it will try up
    until the attempted nickname is 9 characters long.
    """

    def try_nick(self):
        """Try to find a new nickname with a short skirt and a long _."""
        isupport = self.get_extension("ISupport")
        if isupport:
            nicklen = isupport.get("NICKLEN")
        else:
            nicklen = 9  # RFC1459 default

        if len(self.attempt_nick) >= nicklen:
            # Nick is too long! This isn't gonna work.
            raise ValueError("Can't add more underscores")

        return self.attempt_nick + "_"


class NumberSubstituteAlt(BaseAlt):
    """This class attempts to substitute letters for numbers and vis versa.

    This extension will try until all opportunities for leetifying have
    been exhausted.
    """

    leetmap = {
        'A': '4',
        'a': '4',
        'B': '8',
        'E': '3',
        'e': '3',
        'G': '6',
        'g': '9',
        'I': '1',
        'i': '1',
        'O': '0',
        'o': '0',
        'S': '5',
        's': '5',
        'T': '7',
        't': '7',
        '`': '\\',
    }

    unleetmap = {v: k for k, v in leetmap.items()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.index = 0  # The present nick index

    def try_nick(self):
        """Try to find a new nickname by being a 1337 h4x0r."""
        while self.index < len(self.attempt_nick):
            # Try to leetify a letter
            char = self.attempt_nick[self.index]
            if self.index > 0 and char in self.leetmap:
                # Nicks can't begin with any character in leetmap.
                char = self.leetmap[char]
            elif char in self.unleetmap:
                char = self.unleetmap[char]
            else:
                self.index += 1
                continue

            # Munge!
            val = (self.attempt_nick[:self.index] + char +
                   self.attempt_nick[self.index + 1:])
            self.index += 1
            return val

        # If we get here, we've exhausted all other options
        raise ValueError("Cannot become more 1337; alt nicks exhausted.")


class NumberSubstitueAlt(NumberSubstituteAlt):

    """Alias for :py:class:`~PyIRC.extensions.NumberSubstituteAlt`.

    This is around for compatibility purposes. The new class fixes a
    rather embarrassing typo.
    """
