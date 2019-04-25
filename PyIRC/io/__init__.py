# Copyright © 2013-2019 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""I/O backends for PyIRC.

This module contains the I/O backends for PyIRC. The backends inherit from
:py:class:`~PyIRC.base.IRCBase` to pump messages in and out of the library, and
perform scheduling functions.
"""

__all__ = ["asyncio", "socket"]
