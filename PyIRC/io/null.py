# Copyright © 2015 Andrew Wilcox.  All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


""" A null backend, used for testing purposes.  No connections are made. """


from time import sleep
from sched import scheduler
from logging import getLogger

from PyIRC.base import IRCBase
from PyIRC.line import Line


logger = getLogger(__name__)


class NullSocket(IRCBase):

    """ The fake socket implementation of the IRC protocol. """

    def connect(self):
        self.scheduler = scheduler()

        self.recvq = []
        self.sendq = []

        self.disconnect_on_next = False

        super().connect()

    def recv(self):
        if self.disconnect_on_next:
            raise OSError('Connection reset by test.')

        for line in self.recvq:
            logger.debug("IN: %s", str(line).rstrip())
            super().recv(line)
            self.recvq.remove(line)

        return

    def inject_line(self, line):
        """ Inject a Line into the recvq for the client. """
        assert isinstance(Line, line)
        self.recvq.append(line)

    def loop(self):
        """ Simple loop, unchanged from IRCSocket. """
        self.connect()

        while True:
            try:
                self.recv()
            except OSError as e:
                # Connection closed
                self.close()
                raise

    def send(self, command, params):
        line = super().send(command, params)
        if line is None:
            return

        if self.disconnect_on_next:
            raise OSError("Connection reset by peer")

        self.sendq.append(line)
        logger.debug("OUT: %s", str(line).rstrip())

    def draw_line(self):
        """ Draw the earliest Line in the sendq from the client.

        Returns None if there are no lines currently in the sendq. """
        if len(self.sendq) == 0:
            return None

        return self.sendq.pop(0)

    def reset_connection(self):
        """ Emulate a server forcibly disconnecting the client.  Maybe useful
        for ERROR or QUIT. """
        self.disconnect_on_next = True

    def schedule(self, time, callback):
        return self.scheduler.enter(time, 0, callback)

    def unschedule(self, sched):
        self.scheduler.cancel(sched)

    def wrap_ssl(self):
        """ Mock wrapping SSL.  Not sure if this is even useful. """
        if self.ssl:
            # Wrapped already
            return False

        self.ssl = True

        return True
