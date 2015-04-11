# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from collections import OrderedDict, deque
from logging import getLogger

from PyIRC.numerics import Numerics
from PyIRC.event import LineEvent, HookEvent
from PyIRC.hook import HookGenerator, PRIORITY_DONTCARE


logger = getLogger(__name__)


class BaseExtension(metaclass=HookGenerator):
    """ The base class for extensions.

    Hooks may exist in this, in a hclass_hooks dictionary. These can be
    created by hand, but it is recommended to let them be created by the
    HookGenerator metaclass and the `hook` decorator.

    Members:
    
    requires
        required extensions (must be a name)
    priority
        the priority of this extension, lower is higher (like Unix)
    hook_classes
        A Mapping of hclass to an ``Event`` subclass``
    """

    priority = PRIORITY_DONTCARE
    requires = []
    hook_classes = {}

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

    def call_event(self, hclass, event, *args):
        """ Mirror self.base.events.call_event """

        return self.base.events.call_event(hclass, event, *args)

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

        self.create_hooks("commands")
        self.create_hooks("hooks")

    def create_hooks(self, hclass):
        """ Register hooks contained in the given attribute from loaded
        extensions """
        for extension in self.db.values():
            self.events.register_callbacks_from_inst(hclass, extension)

    def create_db(self):
        """ Build the extensions database """
        self.db.clear()
        self.events.clear()

        self.create_default_events()

        # Custom hooks tables
        hook_classes = dict()

        # Create a deque of extensions for easy popping/pushing
        extensions = deque(self.extensions)
        extensions_names = {e.__name__ for e in extensions}
        while extensions:
            # Pop an extension off the head
            extension_class = extensions.popleft()
            extension_name = extension_class.__name__
            if extension_name in self.db:
                # Already present
                continue

            # Create the extension
            extension_inst = extension_class(self.base, **self.kwargs)

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

            # Register extension
            self.db[extension_name] = extension_inst

            # Grab any custom hooks
            hook_classes.update(extension_inst.hook_classes)

        # Create the default hooks
        self.create_default_hooks()

        # Post-load hook
        for hclass, event in hook_classes.items():
            logger.debug("Registering new event class: %s", hclass)
            self.events.register_class(hclass, event)
            self.create_hooks(hclass)

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
                logger.debug("Removing extension: %s", name)
                del self.extensions[i]

        if len(extensions) > len(self.extensions):
            # List length changed
            self.create_db()
            return True

        # Not found
        return False
