# Copyright © 2013-2015 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""IRC daemon specific extensions."""


from collections import namedtuple

from PyIRC.extensions import BaseExtension
from PyIRC.numerics import Numerics
from PyIRC.signal import event

from PyIRC.util.classutil import get_all_subclasses


__all__ = ["base", "hybridfamily", "inspircd"]


Extban = namedtuple("Extban", "negative ban target")
"""A parsed extban."""


BanEntry = namedtuple("BanEntry", "mask settermask setter setdate duration "
                      "reason oreason")
"""A result from a ban lookup.

:attr mask:
    The mask the ban applies to.

:attr settermask:
    Mask of the user who set the ban (``None`` if not known).

:attr setter:
    Nickname or server of the person who set the ban (used in Hybrid
    derivatives).

:attr setdate:
    A ``datetime`` object representing the date and time the ban was set.

:attr duration:
    The duration of the ban, ``None`` for permanent.

:attr reason:
    Reason for the ban. May be ``None``, in which case, there is no reason.

:attr oreason:
    The operator private reason for the ban. May be ``None``. Not all IRC
    daemons support this.
"""


# FIXME this sucks, importing them all here so the subclasses of BaseServer
# are visible
from PyIRC.extensions.ircd import base, hybridfamily, inspircd


class IRCDaemonExtension(BaseExtension):

    """The extension for discovering IRC daemons and loading the correct
    server-specific extension."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.extension_name = None

    @event("commands", Numerics.RPL_VERSION, priority=1000)
    def probe(self, _, line):
        for subclass in get_all_subclasses(base.BaseServer):
            if subclass.provides(self.base):
                self.load_extension(subclass)
                return
