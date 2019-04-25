#!/usr/bin/env python3
# Copyright © 2015-2019 A. Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Automatic SSL negotiation.

It's a little like the ESMTP STARTTLS command, but the server does not
forget all of the client state after it is issued. Therefore, it should
be issued as quickly as possible.
"""


from logging import getLogger

from taillight.signal import SignalDefer

from PyIRC.signal import event
from PyIRC.extensions import BaseExtension
from PyIRC.numerics import Numerics


_logger = getLogger(__name__)  # pylint: disable=invalid-name


class StartTLS(BaseExtension):

    """Support for the STARTTLS extension.

    Not all I/O backends support this, notably
    :py:class:`~PyIRC.io.asyncio` before Python 3.7.
    """

    requires = ["CapNegotiate"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tls_event = None

        if not self.ssl:
            self.caps = {
                "tls": [],
            }

    @event("link", "disconnected")
    def close(self, _):
        """Reset state because we are disconnected."""
        self.tls_event = None

    @event("cap_perform", "ack", priority=-1000)
    def starttls(self, _, line, caps):
        """Respond to TLS CAP acknowledgement."""
        # pylint: disable=unused-argument
        # This must come before anything else in the chain
        if self.ssl:
            # Unnecessary
            return

        if self.tls_event:
            return

        if "tls" in caps:
            self.tls_event = event
            self.send("STARTTLS", None)
            raise SignalDefer()

    @event("commands", Numerics.RPL_STARTTLS)
    def wrap(self, _, line):
        """Actually start TLS communication."""
        # pylint: disable=unused-argument
        _logger.info("Performing STARTTLS initiation...")
        self.wrap_ssl()

        self.resume_event("cap_perform", "ack")

    @event("commands", Numerics.ERR_STARTTLS)
    def abort(self, _, line):
        """Report a problem with TLS communication.

        .. warning::     This allows connection to continue anyway!
        """
        # pylint: disable=unused-argument
        _logger.critical("STARTTLS initiation failed, connection not secure")

        self.resume_event("cap_perform", "ack")
