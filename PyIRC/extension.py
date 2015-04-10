# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from operator import attrgetter
from collections import OrderedDict, deque
from logging import getLogger

from PyIRC.numerics import Numerics
from PyIRC.event import LineEvent, HookEvent


PRIORITY_DONTCARE = 0
PRIORITY_FIRST = -1000
PRIORITY_LAST = 1000


logger = getLogger(__name__)


def hook(hclass, hook, priority=None):
    """ Decorator to add a class hook

    Arguments:
        hclass: hook class to use
        hook: name of the hook to use
        priority: optional priority value of this hook (defaults to the
            class priority)
    """
    def dec(func):
        _hooks = getattr(func, 'hooks', list())

        _hooks.append((hclass, hook, priority))

        func.hooks = _hooks
        return func

    return dec


class HookGenerator(type):

    """ Internal metaclass for hook generation in `BaseExtension`.

    Do not use this unless you know what you are doing and how this works. """

    def __new__(meta, name, bases, dct):
        # Cache all the members with hooks

        hook_caches = dict()

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

        inst = type.__call__(cls, *args, **kwargs)

        # Get hook cache instance (private member)
        member_name = '_{}__hook_caches'.format(cls.__name__)
        hook_caches = getattr(inst, member_name)
        for hclass, hook in hook_caches.items():
            name = '{}_hooks'.format(hclass)

            # Create hooks table
            htable = dict()
            setattr(inst, name, htable)

            # Go through the hooks table, adding bound functions
            for hook_name, (func, priority) in hook.items():
                htable[hook_name] = (getattr(inst, func), priority)

        return inst


class BaseExtension(metaclass=HookGenerator):
    """ The base class for extensions.

    Hooks may exist in this, in a hclass_hooks dictionary. These can be
    created by hand, but it is recommended to let them be created by the
    HookGenerator metaclass and the `hook` decorator.

    Members:
    - requires - required extensions (must be a name)
    - priority - the priority of this extension, lower is higher (like Unix)
    """

    priority = PRIORITY_DONTCARE
    requires = []

    def __init__(self, base, **kwargs):
        self.base = base

    def send(self, command, params):
        """ Mirror self.base.send """

        self.base.send(command, params)

    def schedule(self, time, callback):
        """ Mirror self.base.schedule """

        return self.base.schedule(time, callback)

    def unschedule(self, sched):
        """ Mirror self.base.unschedule """

        self.base.unschedule(sched)

    def get_extension(self, extension):
        """ Mirror self.base.extensions.get_extension """

        return self.base.extensions.get_extension(extension)

    def call_event(self, cls, event, *args):
        """ Mirror self.base.events.call_event """

        return self.base.events.call_event(cls, event, *args)

    def casefold(self, string):
        """ Mirror self.base.casefold """

        return self.base.casefold(string)


# Here to avoid circular dependency
from PyIRC.extensions import extensions_db


class ExtensionManager:

    """ Manage extensions to PyIRC's library, and register their hooks. """

    def __init__(self, base, kwargs, events, extensions=[]):
        """ Initialise the extensions manager

        Arguments:
            base: base instance to pass to each extension
            kwargs: keyword arguments to pass to each extension
            events: the EventManager instance to add hooks to
            extensions: our initial list of extensions
        """

        self.base = base
        self.kwargs = kwargs
        self.events = events
        self.extensions = list(extensions)

        self.db = OrderedDict()

    def create_default_events(self):
        """ Create default events and classes """

        self.events.register_class("commands", LineEvent)
        self.events.register_class("hooks", HookEvent)

    def create_default_hooks(self):
        """ Enumerate present extensions and build the commands and hooks
        cache. """

        commands_key = lambda s : (s.lower() if isinstance(s, str) else
                                   s.value)
        self.create_hooks("commands", commands_key)
        self.create_hooks("hooks")

    def create_hooks(self, cls, key=None):
        """ Register hooks contained in the given attribute from loaded
        extensions """

        attr = cls + '_hooks'

        items = self.db.items()
        for order, (name, extension_inst) in enumerate(items):
            extension_table = getattr(extension_inst, attr, None)
            if extension_table is None:
                continue

            for hook, (callback, priority) in extension_table.items():
                if key:
                    hook = key(hook)

                self.events.register_callback(cls, hook, priority, callback)

    def create_db(self):
        """ Build the extensions database """

        self.db.clear()
        self.events.clear()

        self.create_default_events()

        extensions = deque(self.extensions)
        extensions_names = {e.__name__ for e in extensions}
        while extensions:
            # Pop an extension off the head
            extension_cls = extensions.popleft()
            if extension_cls.__name__ in self.db:
                # Already present
                continue

            # Create the extension
            extension_inst = extension_cls(self.base, **self.kwargs)
            self.db[extension_cls.__name__] = extension_inst

            # Resolve all dependencies
            for require in extension_inst.requires:
                if require in extensions_names:
                    continue

                try:
                    # Push extension to the tail
                    extensions.append(extensions_db[require])
                except KeyError as e:
                    raise KeyError("Required extension not found: {}".format(
                        require)) from e

        # Create the default hooks
        self.create_default_hooks()

        # Post-load hook
        self.events.call_event("hooks", "extension_post")

    def add_extension(self, extension):
        """ Add an extension by name """

        if extension in self.extensions:
            return

        self.extensions.append(extension)
        self.create_db()

    def get_extension(self, extension):
        """ Get an extension by name, or return None """

        return self.db.get(extension)

    def remove_extension(self, extension):
        """ Remove a given extension by name """

        extensions = list(self.extensions)
        for i, name in enumerate(e.__name__ for e in extensions):
            if name == extension:
                logger.debug("Removing extension: %s")
                del self.extensions[i]

        if len(extensions) > len(self.extensions):
            # List length changed
            self.create_db()
            return True

        # Not found
        return False
