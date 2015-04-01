#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


from base import BaseExtension
from numerics import Numerics


class ISupport(BaseExtension):

    """ Parse ISUPPORT attributes into useful things """

    def __init__(self, base, **kwargs):
        self.base = base

        self.implements = {
            Numerics.RPL_ISUPPORT : self.parse_isupport,
        }

        # State
        self.base.supported = {}

    def parse_isupport(self, line):
        supported = self.base.supported

        for param in line.params[-1]:
            # Split into key : value pair
            key, _, value = param.split('=')

            if not value:
                supported[key] = True
                continue

            # Parse into CSV
            value = value.split(',')

            # For each value, parse into pairs of val : data
            # If val is blank but we have a separator, extend the last value.
            # (Works around a charybdis and ratbox bug)
            extend = None
            for i, v in enumerate(value):
                val, sep, data = v.partition(':')
                if sep:
                    if data:
                        extend = data
                    else:
                        data = extend

                    value[i] = (val, data)

            supported[key] = value
