# Copyright © 2013-2015 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Latency measurements to the server."""


try:
    # NB - this import cannot fail on Py3.4+
    from time import monotonic as time
except ImportError:
    from time import time


from PyIRC.signal import event
from random import randint, choice
from string import ascii_letters as letters, digits
from logging import getLogger

from PyIRC.extension import BaseExtension
from PyIRC.numerics import Numerics


_logger = getLogger(__name__)


class LagCheck(BaseExtension):

    """Lag measurement extension. Checks latency periodically.

    :ivar lag:
        Current lag measurements from the server, measured in seconds. It is
        not advisable to rely on less than a millisecond of precision on most
        systems and real-world networks.

    """

    def __init__(self, *args, **kwargs):
        """Initialise the LagCheck extension.

        :key lagcheck:
            Time interval to do periodic lag checks to update the lag timer.
            Defaults to 15 seconds. Setting the value too low may result in
            being disconnected by the server.

        """
        super().__init__(*args, **kwargs)

        self.lagcheck = kwargs.get("lagcheck", 15)

        self.lag = None

        self.last = None
        self.timer = None

    @staticmethod
    def timestr(time):
        """Return a random string based on the current time."""

        length = randint(5, 10)
        chars = letters + digits
        randstr = ''.join(choice(chars) for x in range(length))

        return "{}-{}".format(time, randstr)

    def ping(self):
        """Callback for ping."""

        if self.last is not None:
            raise OSError("Connection timed out")

        self.last = time()
        s = self.timestr(self.last)
        self.send("PING", [s])
        self.timer = self.schedule(self.lagcheck, self.ping)

    @event("hooks", "disconnected")
    def close(self, caller):
        self.last = None
        self.lag = None

        if self.timer is not None:
            try:
                self.unschedule(self.timer)
            except ValueError:
                pass

    @event("commands", Numerics.RPL_WELCOME)
    def start(self, caller, line):
        """Begin sending PING requests as soon as possible."""

        self.ping()

    @event("commands", "PONG")
    def pong(self, caller, line):
        """Use PONG reply to check lag."""

        if self.last is None:
            return

        t, sep, s = line.params[-1].partition('-')
        if not sep or not s:
            return

        if t != str(self.last):
            return

        self.lag = round(time() - float(self.last), 3)
        self.last = None
        _logger.info("Lag: %f", self.lag)
