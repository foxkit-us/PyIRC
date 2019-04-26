# Copyright © 2013-2019 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


"""Support for asyncio, available in Python 3.4 and later (and 3.3 via a
backport)."""


from sys import version_info

import asyncio
import ssl

from collections import namedtuple
from functools import update_wrapper, partial
from logging import getLogger

from PyIRC.base import IRCBase, Event
from PyIRC.line import Line


_logger = getLogger(__name__)  # pylint: disable=invalid-name


class IRCProtocol(IRCBase, asyncio.Protocol):

    """The asyncio implementation of the IRC protocol. Available only with
    Python 3.4 and above in the standard library.

    The same methods as :py:class:`~PyIRC.base.IRCBase` are available.

    .. warning:
        This module will not work with StartTLS unless your Python version is
        3.7 or newer, due to limitations in the asyncio module. If your Python
        version is less than 3.7, this will unload StartTLS if found. See the
        relevant `asyncio bug`_ for more information.

    .. _`asyncio bug`: https://bugs.python.org/issue23749
    """

    _ScheduleItem = namedtuple("_ScheduleItem", "time callback sched")

    def __init__(self, *args, **kwargs):
        self._call_queue = asyncio.Queue()

        # Start the task queue
        self._call_task = asyncio.ensure_future(self._process_queue())
        self._call_task.add_done_callback(self._process_queue_exit)

        super().__init__(*args, **kwargs)

        self.sched_events = set()

        self.data = None

        self.transport = None

        # Python versions before 3.7 are not compatible with StartTLS.
        if version_info < (3, 7):
            self.unload_extension("StartTLS")
            _logger.critical("Removing StartTLS extension due to asyncio " \
                             "limitations; please upgrade to Python 3.7 or \
                             later.")

    def connect(self):
        """Create a connection.

        :returns:
            An asyncio coroutine representing the connection.
        """
        loop = asyncio.get_event_loop()
        return loop.create_connection(lambda: self, self.server, self.port,
                                      ssl=self.ssl, local_addr=self.bindport)

    def close(self):
        super().close()

        # Clear the queue
        self._call_queue = asyncio.Queue()

        # XXX it's in this order for backwards compat
        for sched in self.sched_events:
            self.unschedule(sched)

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
            _logger.debug("IN: %s", str(line).rstrip())
            try:
                super().recv(line)
            except Exception:
                # We should never get here!
                _logger.exception("Exception received in recv loop")
                self.send("QUIT", ["Exception received!"])
                self.transport.close()

                # This is fatal and needs to be reported so stop the event
                # loop.
                loop = asyncio.get_event_loop()
                loop.stop()

                raise

    def connection_closed(self, exc):
        """Handle an abrupt disconnection."""
        _logger.info("Connection lost: %s", str(exc))
        super().close()

    def send(self, command, params):
        line = super().send(command, params)
        if line is None:
            return

        self.transport.write(bytes(line))
        _logger.debug("OUT: %s", str(line).rstrip())

    @asyncio.coroutine
    def _process_queue(self):
        while True:
            cor, future = yield from self._call_queue.get()
            ret = yield from cor
            future.set_result(ret)

    # pylint: disable=unused-argument
    def _process_queue_exit(self, future):
        _logger.critical("Process queue died!")
        self._call_queue = asyncio.Queue()
        self.close()

    def call_event(self, hclass, event, *args, **kwargs):
        """Call an (hclass, event) signal.

        If no args are passed in, and the signal is in a deferred state,
        the arguments from the last call_event will be used.
        """
        if self._call_task.done() and self._call_task.exception():
            # Exception raised, let's get out of here!
            raise self._call_task.exception()

        signal = self.signals.get_signal((hclass, event))
        event = Event(signal.name, self)

        co = signal.call_async(event, *args, **kwargs)
        future = asyncio.Future()

        self._call_queue.put_nowait((co, future))

        return (event, future)

    def schedule(self, time, callback):
        def cb_cleanup(time, callback):
            self.sched_events.discard((time, callback))
            return callback()

        callback_wrap = partial(cb_cleanup, time, callback)
        update_wrapper(callback_wrap, callback)

        loop = asyncio.get_event_loop()
        val = loop.call_later(time, callback_wrap)
        return self._ScheduleItem(time, callback, val)

    def unschedule(self, sched):
        self.sched_events.discard((sched.time, sched.callback))
        sched.sched.cancel()

    def wrap_ssl(self):
        if version_info < (3, 7):
            raise NotImplementedError("Cannot wrap SSL after connect due " \
                                      "to asyncio limitations; please " \
                                      "upgrade to Python 3.7 or later.")

        loop = asyncio.get_event_loop()
        co = loop.start_tls(self.transport, self, ssl.create_default_context())
        future = asyncio.Future()
        self._call_queue.put_nowait((co, future))
