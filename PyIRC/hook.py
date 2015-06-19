# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from inspect import getmembers, ismethod
from logging import getLogger

from PyIRC.util.classutil import private_mangle

logger = getLogger(__name__)


PRIORITY_DONTCARE = 0
"""Hook can run whenever it wants"""

PRIORITY_FIRST = -1000
"""Hook should run first"""

PRIORITY_LAST = 1000
"""Hook should run last"""


def hook(hclass, hook, priority=None):
    """Decorator to add a class hook

    :param hclass:
        hook class to use

    :param hook:
        name of the hook to use

    :param priority:
        optional priority value of this hook (defaults to the class
        priority)
    """
    def dec(func):
        _hooks = getattr(func, 'hooks', list())
        _hooks.append((hclass, hook, priority))
        func.hooks = _hooks
        return func

    return dec


def _hook_pred(member):
    return ismethod(member) and hasattr(member, "hooks")


def build_hook_table(instance):
    """Build the hook tables for a class
    
    .. warning::
        This creates foo_hooks variables for each instance! If you use
        __slots__ you *MUST* have a foo_hooks for each hclass you use.
    """
    for meth in getmembers(instance, _hook_pred):
        meth = meth[1]  # Don't care about the name
        for (hclass, hook, priority) in meth.hooks:
            hname = "{}_hooks".format(hclass)
            htable = getattr(instance, hname, dict())
            if not htable:
                setattr(instance, hname, htable)

            if priority is None:
                priority = PRIORITY_DONTCARE

            htable[hook] = meth, priority
