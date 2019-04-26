# Copyright © 2013-2019 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Server time delta measurements."""


from datetime import datetime, timezone
from logging import getLogger

from PyIRC.signal import event
from PyIRC.extensions import BaseExtension
from PyIRC.numerics import Numerics


_logger = getLogger(__name__)  # pylint: disable=invalid-name


class TimeDelta(BaseExtension):

    """Server time delta measurements.

    Provides a rough time difference between local and server time.

    Requires :py:class:`~PyIRC.extensions.lag.LagCheck` to be loaded.

    :ivar delta:
        Current time delta measurement between server and client, computed as
        the difference between local time and server time. There is no
        guarantee the delta measurement will be accurate, but it should be
        accurate to within a few seconds under ideal conditions. Jitter may
        cause this value to be inaccurate. If the delta is high, you should
        check your local time, or contact an administrator on the server and
        let them know their time is out of sync. If the delta is set to `None`,
        then a delta measurement has not yet been performed (or cannot be).

    :ivar broken:
        Set to `True` if the server's time functionality is broken in some way.
        You may have to adjust `strptime_fmt` if it is. If it is set to
        `False`, the server's time functionality works fine. `None` is an
        indeterminate state.
    """

    requires = ["LagCheck"]

    def __init__(self, *args, **kwargs):
        """Initialise the TimeDelta extension.

        :key deltacheck:
            Time interval to do periodic delta checks to update the time delta
            value. Defaults to 300 seconds.

        :key strptime_fmt:
            Format passed to `strptime` for date processing. This may have to
            be changed for your server. The default should work for most
            servers.
        """
        super().__init__(*args, **kwargs)

        self.deltacheck = kwargs.get("deltacheck", 300)
        self.strptime_fmt = kwargs.get("strptime_fmt",
                                       "%A %B %d %Y -- %H:%M:%S %z")
        self.delta = None
        self.broken = None
        self.timer = None

    def time_callback(self):
        """Callback for time."""
        if self.broken:
            return

        self.send("TIME", [])
        self.timer = self.schedule(self.deltacheck, self.time)

    @event("link", "disconnected")
    def close(self, _):
        """Reset state since we are disconnected."""
        self.delta = None
        self.broken = None

        if self.timer is not None:
            try:
                self.unschedule(self.timer)
            except ValueError:
                pass
        
        self.timer = None

    # pylint: disable=unused-argument
    # This should come after LagCheck hooks this, but it's not essential
    @event("commands", "PONG", priority=100)
    def start(self, _, line):
        """Begin sending delta requests after our first PONG reply."""
        if self.timer is None:
            self.time_callback()

    @event("commands", Numerics.RPL_TIME)
    def time_response(self, _, line):
        """Process RPL_TIME event."""
        if self.broken:
            # No use in trying if it doesn't work
            return

        try:
            server_ts = datetime.strptime(line.params[-1], self.strptime_fmt)
        except ValueError as exc:
            _logger.warning("strptime format may be wrong (error: %s)",
                            str(exc))
            self.broken = True
            if self.timer is not None:
                try:
                    self.unschedule(self.timer)
                except ValueError:
                    pass

            return

        self.broken = False
        our_ts = datetime.now(timezone.utc)
        delta = (our_ts - server_ts).seconds

        # Correction for lag
        lag = self.get_extension("LagCheck")
        if lag.lag:
            delta -= lag.lag

        self.delta = delta
