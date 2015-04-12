# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from logging import getLogger

from PyIRC.util.classutil import private_mangle


logger = getLogger(__name__)


"""Hook can run whenever it wants"""
PRIORITY_DONTCARE = 0

"""Hook should run first"""
PRIORITY_FIRST = -1000

"""Hook should run last"""
PRIORITY_LAST = 1000


def hook(hclass, hook, priority=None):
    """ Decorator to add a class hook

    This works with `HookGenerator` to generate the hook tables used by
    ``EventManager``.

    Arguments:
        hclass
            hook class to use

        hook
            name of the hook to use

        priority
            optional priority value of this hook (defaults to the class
            priority)
    """
    def dec(func):
        _hooks = getattr(func, 'hooks', list())

        _hooks.append((hclass, hook, priority))

        func.hooks = _hooks
        return func

    return dec


class HookGenerator(type):

    """Internal metaclass for hook generation in BaseExtension.

    This generates hook tables and does runtime binding of the hooks, to
    enable dynamic generation of the tables with no user intervention.

    Do not use this unless you know what you are doing and how this works.
    """

    def __new__(meta, name, bases, dct):
        # Cache all the members with hooks

        hook_caches = dict()

        if len(bases) > 0:
            cared_about = [b for b in bases if b.__name__ != 'BaseExtension']
            for ext in cared_about:
                # we merge each extension's hooks in, using the highest
                # priority hook on conflict.
                dname = private_mangle(ext, '__hook_caches')
                curr_caches = getattr(ext, dname, None)
                if curr_caches is None: continue
                for hclass, cache in curr_caches.items():
                    hdict = hook_caches.get(hclass)
                    if hdict is None:
                        hook_caches[hclass] = cache
                        continue
                    for hook in cache.keys():
                        if hook in hdict and hdict[hook][1] < cache[hook][1]:
                            continue
                        else:
                            hdict[hook] = cache[hook]

        for key, val in dct.items():
            if key.startswith('__') or not callable(val):
                continue

            _hooks = getattr(val, 'hooks', None)
            if not _hooks:
                continue

            for hclass, hook, priority in _hooks:
                # Build the hooks cache
                hdict = hook_caches.get(hclass)
                if hdict is None:
                    hdict = hook_caches[hclass] = dict()

                if priority is None:
                    # Set to class default priority
                    priority = dct.get('priority', PRIORITY_DONTCARE)

                hdict[hook] = (key, priority)

        # Private member
        member_name = '_{}__hook_caches'.format(name)
        dct[member_name] = hook_caches

        return super(HookGenerator, meta).__new__(meta, name, bases, dct)

    def __call__(cls, *args, **kwargs):
        # Bind the names from the hook cache to the instance

        logger.debug("Binding: %s", cls.__name__)

        inst = type.__call__(cls, *args, **kwargs)

        # Get hook cache instance (private member)
        hook_caches = getattr(inst, private_mangle(inst, '__hook_caches'))
        for hclass, hook in hook_caches.items():
            name = '{}_hooks'.format(hclass)

            # Create hooks table
            htable = dict()
            setattr(inst, name, htable)

            # Go through the hooks table, adding bound functions
            for hook_name, (func, priority) in hook.items():
                logger.debug("Bound: %s (%s): %r", hclass, hook_name, func)
                htable[hook_name] = (getattr(inst, func), priority)

        return inst

