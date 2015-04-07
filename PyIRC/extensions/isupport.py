#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


from logging import getLogger


from PyIRC.base import BaseExtension
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


class ISupport(BaseExtension):

    """ Parse ISUPPORT attributes into useful things """

    def __init__(self, base, **kwargs):
        self.base = base

        self.commands = {
            Numerics.RPL_ISUPPORT : self.parse_isupport,
        }

        self.hooks = {
            "disconnected" : self.close,
        }

        # State
        self.supported = {}

    def close(self, event):
        self.supported.clear()

    def parse_isupport(self, event):
        supported = self.supported

        for param in event.line.params[1:-1]:
            # Split into key : value pair
            key, _, value = param.partition('=')

            if not value:
                logger.debug("ISUPPORT [k]: %s", key)
                supported[key] = True
                continue

            # Parse into CSV
            value = value.split(',')

            # For each value, parse into pairs of val : data
            for i, v in enumerate(value):
                val, sep, data = v.partition(':')
                if sep:
                    if not data:
                        data = None

                    value[i] = (val, data)

            if len(value) == 1:
                # Single key
                value = value[0]

            logger.debug("ISUPPORT [k:v]: %s:%r", key, value)
            supported[key] = value
