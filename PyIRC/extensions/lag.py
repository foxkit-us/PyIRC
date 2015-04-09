# Copyright © 2013-2015 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.

""" Lag analysis and checking """


from PyIRC.extension import BaseExtension, hook
from PyIRC.numerics import Numerics

try:
    from time import monotonic as time
except ImportError:
    from time import time

from random import randint, choice
from string import ascii_letters as letters, digits
from logging import getLogger


logger = getLogger(__name__)


class LagCheck(BaseExtension):

    """ Lag measurement extension

    Members:
    - lag: current lag measurements from the server
    """

    def __init__(self, base, **kwargs):

        self.base = base

        self.lagcheck = kwargs.get("lagcheck", 30)

        self.last = None
        self.lag = None
        self.timer = None

    @staticmethod
    def timestr(time):
        """ Return a random string based on the current time """

        length = randint(5, 10)
        chars = letters + digits
        randstr = ''.join(choice(chars) for x in range(length))

        return "{}-{}".format(time, randstr)

    def ping(self):
        """ Callback for ping """

        if self.last is not None:
            raise OSError("Connection timed out")

        self.last = time()
        s = self.timestr(self.last)
        self.send("PING", [s])
        self.timer = self.schedule(self.lagcheck, self.ping)

    @hook("hooks", "close")
    def close(self, event):
        self.last = None
        self.lag = None

        if self.timer is not None:
            try:
                self.unschedule(self.timer)
            except ValueError:
                pass

    @hook("commands", Numerics.RPL_WELCOME)
    def start(self, event):
        """ Begin sending PING requests as soon as possible """

        self.ping()

    @hook("commands", "PONG")
    def pong(self, event):
        """ Use PONG reply to check lag """

        if self.last is None:
            return

        t, sep, s = event.line.params[-1].partition('-')
        if not sep or not s:
            return

        if t != str(self.last):
            return

        self.lag = round(time() - float(self.last), 3)
        self.last = None
        logger.info("Lag: %f", self.lag)

