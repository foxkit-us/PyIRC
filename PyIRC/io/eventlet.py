# Copyright © 2013-2015 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


"""An eventlet I/O backend for PyIRC.

This uses green threads to do scheduling of callbacks, and uses eventlet
sockets.

:py:meth:`~PyIRC.io.IRCEventlet.connect` is a green thread, and all
of the scheduling is done with eventlet's `spawn_after`.

"""


from eventlet.green import socket, ssl
from eventlet import spawn_after, spawn_n

from logging import getLogger

from PyIRC.base import IRCBase
from PyIRC.line import Line


_logger = getLogger(__name__)  # pylint: disable=invalid-name


class IRCEventlet(IRCBase):

    """The eventlet implementation of the IRC protocol. Everything is done
    with green threads, as far as possible.

    Virtually everything can be done as a green thread.

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        family = kwargs.get("family", socket.AF_INET)

        self.socket = socket.socket(family=family)

        # Set up the scheduler now as it sends events
        self.scheduler = scheduler()

        # Data for the socket
        self.data = b''

    def connect(self):
        if self.ssl:
            self._socket = self.socket
            if self.ssl is True:
                self.socket = ssl.wrap_socket(self.socket)
            else:
                # self.ssl is an externally-created SSLContext
                # pylint: disable=no-member
                self.socket = self.ssl.wrap_socket(self.socket)

        self.socket.settimeout(self.kwargs.get("socket_timeout", 10))
        self.socket.connect((self.server, self.port))

        super().connect()

    def recv(self):
        timeout = self.kwargs.get('recv_timeout', None)
        self.socket.settimeout(timeout)
        try:
            data = self.socket.recv(512)
            if not data:
                raise OSError("Connection reset by peer")

            data = self.data + data
        except socket.timeout:
            return

        lines = data.split(b'\r\n')
        self.data = lines.pop()

        for line in lines:
            line = Line.parse(line.decode('utf-8', 'ignore'))
            _logger.debug("IN: %s", str(line).rstrip())
            spawn_n(super().recv(line))

    def loop(self):
        """Simple loop for bots.

        Does not return, but raises exception when the connection is
        closed.

        """
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

        self.socket.settimeout(self.kwargs.get('send_timeout', None))
        if self.socket.send(bytes(line)) == 0:
            raise OSError("Connection reset by peer")

        _logger.debug("OUT: %s", str(line).rstrip())

    def schedule(self, time, callback):
        return spawn_after(time, callback)

    def unschedule(self, sched):
        sched.cancel()

    def wrap_ssl(self):
        if self.ssl:
            # Wrapped already
            return False

        self._socket = self.socket
        self.socket = ssl.wrap_socket(self.socket)
        self.socket.do_handshake()
        self.ssl = True

        return True
