#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from logging import getLogger

from PyIRC.extension import BaseExtension, hook
from PyIRC.numerics import Numerics
from PyIRC.auxparse import isupport_parse


logger = getLogger(__name__)


class ISupport(BaseExtension):

    """ Parse ISUPPORT attributes into useful things.

    Parsing is done according to auxparse.isupport_parse semantics.

    The following attributes are available:

    supported
        parsed ISUPPORT data from the server. Do note that because ISUPPORT is
        technically non-standard, users should be prepared for data that does
        not conform to any implied standard.
    """

    def __init__(self, base, **kwargs):
        self.base = base

        # State
        self.supported = {}

    @hook("hooks", "disconnected")
    def close(self, event):
        self.supported.clear()

    @hook("commands", Numerics.RPL_ISUPPORT)
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

