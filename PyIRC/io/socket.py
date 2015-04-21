# Copyright © 2013-2015 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


""" A basic socket/ssl/sched-based module implementation for IRC.

If you just want a simple bot for one network, this is what you want.

Note all socket stuff is blocking, if you want non-blocking operation, you
may want to subclass this and modify things for your application.

This also serves as a useful example.
"""


import socket
import ssl

from time import sleep
from sched import scheduler
from logging import getLogger

from PyIRC.base import IRCBase
from PyIRC.line import Line


logger = getLogger(__name__)


class IRCSocket(IRCBase):

    """The socket implementation of the IRC protocol. No asynchronous I/O is
    done. All scheduling is done with socket timeouts and the python ``sched``
    module.

    The same methods available in
    :py:class:`~PyIRC.base.IRCBase` are available.


    :key socket_timeout:
        Set the timeout for connecting to the server (defaults to 10)

    :key send_timeout:
        Set the timeout for sending data (default None)

    :key recv_timeout:
        Set the timeout for receiving data (default None)

    :key family:
        The family to use for the socket (default AF_INET, IPv4). Set to
        socket.AF_INET6 for IPv6 usage.
    """

    def connect(self):
        family = self.kwargs.get("family", socket.AF_INET)

        self.socket = socket.socket(family=family)

        if self.ssl:
            self._socket = self.socket
            if self.ssl is True:
                self.socket = ssl.wrap_socket(self.socket)
            else:
                self.socket = self.ssl.wrap_socket(self.socket)

        self.socket.settimeout(self.kwargs.get("socket_timeout", 10))
        self.socket.connect((self.server, self.port))

        # Set up the scheduler now as it sends events
        self.scheduler = scheduler()

        # Data for the socket
        self.data = b''

        super().connect()

    def recv(self):
        timeout = self.kwargs.get('recv_timeout', None)

        if not self.scheduler.empty():
            timeout_s = self.scheduler.run(False)
            if timeout is None or timeout > timeout_s:
                timeout = timeout_s

        self.socket.settimeout(timeout)
        try:
            data = self.socket.recv(512)
            if not data:
                raise OSError("Connection reset by peer")

            data = self.data + data
        except socket.timeout:
            # XXX should try harder to meet user timeout deadlines and not
            # quit early.
            return

        lines = data.split(b'\r\n')
        self.data = lines.pop()

        for line in lines:
            line = Line.parse(line.decode('utf-8', 'ignore'))
            logger.debug("IN: %s", str(line).rstrip())
            super().recv(line)

    def loop(self):
        """Simple loop for bots.

        Does not return, but raises exception when the connection is closed.
        """
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

        self.socket.settimeout(self.kwargs.get('send_timeout', None))
        if self.socket.send(bytes(line)) == 0:
            raise OSError("Connection reset by peer")

        logger.debug("OUT: %s", str(line).rstrip())

    def schedule(self, time, callback):
        return self.scheduler.enter(time, 0, callback)

    def unschedule(self, sched):
        self.scheduler.cancel(sched)

    def wrap_ssl(self):
        if self.ssl:
            # Wrapped already
            return False

        self._socket = self.socket
        self.socket = ssl.wrap_socket(self.socket)
        self.socket.do_handshake()
        self.ssl = True

        return True
