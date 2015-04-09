#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from logging import getLogger

from PyIRC.extension import BaseExtension
from PyIRC.numerics import Numerics
from PyIRC.auxparse import isupport_parse


logger = getLogger(__name__)


class ISupport(BaseExtension):

    """ Parse ISUPPORT attributes into useful things.

    Members:
    - supported: parsed ISUPPORT data from the server. Because ISUPPORT is
      technically non-standard, users should be prepared for unexpected data.
    """

    def __init__(self, base, **kwargs):
        self.base = base

        self.commands = {
            Numerics.RPL_ISUPPORT : self.isupport,
        }

        self.hooks = {
            "disconnected" : self.close,
        }

        # State
        self.supported = {}

    def close(self, event):
        self.supported.clear()

    def isupport(self, event):
        """ Handle ISUPPORT event """

        # To differentiate between really old ircd servers
        # (RPL_BOUNCE=005 on those)
        if not event.line.params[-1].endswith('server'):
            logger.warning("Really old IRC server detected!")
            logger.warning("It's probably fine but things might break.")
            return

        values = event.line.params[1:-1]
        self.supported.update(isupport_parse(values))

