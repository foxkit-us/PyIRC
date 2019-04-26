# Copyright © 2013-2019 A. Wilcox.  All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


"""A null backend, used for testing purposes.

No connections are made.
"""


from logging import getLogger
from queue import Empty, Queue
from sched import scheduler

from PyIRC.base import IRCBase
from PyIRC.line import Line


_logger = getLogger(__name__)  # pylint: disable=invalid-name


class NullSocket(IRCBase):

    """The fake socket implementation of the IRC protocol."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scheduler = scheduler()

        self.recvq = Queue()
        self.sendq = Queue()

        self.disconnect_on_next = False

    def recv(self):
        if self.disconnect_on_next:
            raise OSError('Connection reset by test.')

        line = self.recvq.get()
        _logger.debug("IN: %s", str(line).rstrip())
        super().recv(line)

    def inject_line(self, line):
        """Inject a Line into the recvq for the client."""
        assert isinstance(line, Line)
        self.recvq.put(line)
        self.recv()

    def loop(self):
        """Simple loop, unchanged from IRCSocket."""
        self.connect()

        while True:
            try:
                self.recv()
            except OSError:
                # Connection closed
                self.close()
                raise

    def send(self, command, params):
        line = super().send(command, params)
        if line is None:
            return

        if self.disconnect_on_next:
            raise OSError("Connection reset by peer")

        self.sendq.put(line)
        _logger.debug("OUT: %s", str(line).rstrip())

    def draw_line(self):
        """Draw the earliest Line in the sendq from the client.

        Returns None if there are no lines currently in the sendq.
        """
        try:
            return self.sendq.get()
        except Empty:
            return None

    def reset_connection(self):
        """Emulate a server forcibly disconnecting the client.

        Maybe useful for ERROR or QUIT.
        """
        self.disconnect_on_next = True

    def schedule(self, time, callback):
        return self.scheduler.enter(time, 0, callback)

    def unschedule(self, sched):
        self.scheduler.cancel(sched)

    def wrap_ssl(self):
        """Mock wrapping SSL.

        Not sure if this is even useful.
        """
        if self.ssl:
            # Wrapped already
            return False

        self.ssl = True

        return True
