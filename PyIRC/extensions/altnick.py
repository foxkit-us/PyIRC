# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Some alternate nick handlers.

This contains an underscore-appending handler and a number-substituting
(leetifying) handler.

"""


from logging import getLogger

from taillight.signal import SignalStop

from PyIRC.signal import event
from PyIRC.numerics import Numerics
from PyIRC.extensions import BaseExtension


_logger = getLogger(__name__)  # pylint: disable=invalid-name


class UnderscoreAlt(BaseExtension):
    """This class attempts to append underscores to the nickname.

    If :py:class:`~PyIRC.extensions.ISupport` is present, it will try until
    the maximum nick length is reached; otherwise, it will try 5 times.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.attempt_nick = self.nick  # from base
        self.attempts = 0

    @event("commands", Numerics.ERR_NICKNAMEINUSE, priority=-1000)
    @event("commands", Numerics.ERR_ERRONEOUSNICKNAME, priority=-1000)
    @event("commands", Numerics.ERR_NONICKNAMEGIVEN, priority=-1000)
    def change_nick(self, _, line):
        if self.registered:
            # Don't care!
            raise SignalStop()

        isupport = self.get_extension("ISupport")
        if not isupport:
            if self.attempts_count >= 5:
                # Give up, but maybe something else can try...
                return
        elif len(self.attempt_nick) == isupport.get("NICKLEN"):
            # Nick is too long! This isn't gonna work.
            return

        self.attempt_nick += '_'
        self.attempts += 1
        self.send("NICK", [self.attempt_nick])
        raise SignalStop()


class NumberSubstitueAlt(BaseExtension):
    """This class attempts to substitute letters for numbers and vis versa.

    This extension will try until all opportunities for leetifying have been
    exhausted.

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

        self.attempt_nick = self.nick  # from base
        self.index = 0  # The present nick index

    @event("commands", Numerics.ERR_NICKNAMEINUSE, priority=-1000)
    @event("commands", Numerics.ERR_ERRONEOUSNICKNAME, priority=-1000)
    @event("commands", Numerics.ERR_NONICKNAMEGIVEN, priority=-1000)
    def change_nick(self, _, line):
        if self.registered:
            # Don't care!
            raise SignalStop()

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
            self.attempt_nick = (self.attempt_nick[:self.index] + char +
                                 self.attempt_nick[self.index + 1:])
            self.send("NICK", [self.attempt_nick])
            self.index += 1
            raise SignalStop()
