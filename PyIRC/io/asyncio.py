# Copyright © 2013-2015 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


"""Support for asyncio, available in Python 3.4 and later (and 3.3 via a
backport).
"""


try:
    import asyncio
except ImportError as e:
    from sys import version_info
    if version_info < (3, 3):
        raise ImportError("Must have Python 3.3 or greater to use this " \
                          "module") from e
    else:
        raise ImportError("Must install asyncio module from PyPI") from e

from logging import getLogger

from PyIRC.base import IRCBase
from PyIRC.line import Line


logger = getLogger(__name__)


class IRCProtocol(IRCBase, asyncio.Protocol):

    """The asyncio implementation of the IRC protocol. Available only with
    Python 3.4 and above in the standard library, and 3.3 via an external
    module.

    The same methods as :py:class:`~PyIRC.base.IRCBase` are available.

    .. warning:
        This module is incompatible with StartTLS, and will unload that
        extension if found! This is a known `asyncio bug`_ and will be fixed
        in the future.

    .. _`asyncio bug`: https://bugs.python.org/issue23749
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Sadly we are not compatible with StartTLS because of a deficiency in
        # Python 3.4/3.5. See https://bugs.python.org/issue23749
        # Once it's fixed, it's okay to remove this whole __init__ function.
        if self.extensions.remove_extension("StartTLS"):
            logger.critical("Removing StartTLS extension due to asyncio " \
                            "limitations")

    def connect(self):
        loop = asyncio.get_event_loop()
        return loop.create_connection(lambda : self, self.server, self.port,
                                      ssl=self.ssl)

    def connection_made(self, transport):
        self.transport = transport
        self.data = b''
        super().connect()

    def data_received(self, data):
        data = self.data + data

        lines = data.split(b'\r\n')
        self.data = lines.pop()

        for line in lines:
            line = Line.parse(line.decode('utf-8', 'ignore'))
            logger.debug("IN: %s", str(line).rstrip())
            try:
                super().recv(line)
            except Exception as e:
                # We should never get here!
                self.send("QUIT", ["Exception received!"])
                self.transport.close()
                raise

    def connection_closed(self, exc):
        logger.info("Connection lost: %s", str(e))
        super().close()

    def send(self, command, params):
        line = super().send(command, params)
        if line is None:
            return

        self.transport.write(bytes(line))
        logger.debug("OUT: %s", str(line).rstrip())

    def schedule(self, time, callback):
        loop = asyncio.get_event_loop()
        return loop.call_later(time, callback)

    def unschedule(self, sched):
        sched.cancel()

    def wrap_ssl(self):
        raise NotImplementedError("Cannot wrap SSL after connect due to " \
                                  "asyncio limitations (see " \
                                  "https://bugs.python.org/issue23749)")
