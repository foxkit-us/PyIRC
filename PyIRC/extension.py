# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from collections import OrderedDict, deque
from functools import lru_cache
from logging import getLogger

from PyIRC.event import LineEvent, HookEvent
from PyIRC.extensions import ExtensionsDatabase
from PyIRC.hook import build_hook_table, PRIORITY_DONTCARE
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


class BaseExtension:

    """ The base class for extensions.

    Hooks may exist in this, in a hclass_hooks dictionary. These can be
    created by hand, but it is recommended to let them be created by the
    :py:class:`~PyIRC.hook.build_hook_table` function and the hook decorator.

    Any unknown attributes in this class are redirected to the ``base``
    attribute.
    """
    
    priority = PRIORITY_DONTCARE
    """The priority of this extension, lower is higher (like Unix)"""

    requires = []
    """Required extensions (must be a name)"""

    hook_classes = {}
    """A Mapping of hclass to an :py:class:`~PyIRC.event.Event` subclass"""

    def __init__(self, base, **kwargs):
        """Initalise the BaseExtension instance.

        :param base:
            Base class for this method
        """
        self.base = base
        build_hook_table(self)

    def __getattr__(self, attr):
        return getattr(self.base, attr)


class ExtensionManager:

    """ Manage extensions to PyIRC's library, and register their hooks. """

    def __init__(self, base, kwargs, events, extensions=[], database=None):
        """Initialise the extensions manager

        :param base:
            Base instance to pass to each extension.

        :param kwargs:
            Keyword arguments to pass to each extension.

        :param events:
            The py:class:`~PyIRC.event.EventManager` instance to add hooks to.

        :param extensions:
            Initial list of extensions.

        :param database:
            Optional extensions database to use.
        """

        self.base = base
        self.kwargs = kwargs
        self.events = events

        if database is not None:
            self.default_db = database
        else:
            self.default_db = ExtensionsDatabase()
        
        # Serialise the extensions list into real extensions classes
        # Strings are looked up in the extensions database
        self.extensions = [self.default_db[e] if isinstance(e, str) else e
                           for e in extensions]

        self.db = OrderedDict()

    def create_default_events(self):
        """Create default events and classes"""
        self.events.register_class("commands", LineEvent)
        self.events.register_class("commands_out", LineEvent)
        self.events.register_class("hooks", HookEvent)

    def create_default_hooks(self):
        """Enumerate present extensions and build the commands and hooks
        cache."""

        self.create_hooks("commands")
        self.create_hooks("commands_out")
        self.create_hooks("hooks")

    def create_hooks(self, hclass):
        """Register hooks contained in the given attribute from loaded
        :param extensions:

        Arguments:

        :param hclass:
            Class to create hooks for
        """
        for extension in self.db.values():
            self.events.register_callbacks_from_inst(hclass, extension)

    def create_db(self):
        """Build the extensions database"""
        self.db.clear()
        self.events.clear()
        self.get_extension.cache_clear()

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
                    extensions.append(self.default_db[require])
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
        """Add an extension by class

        .. warning::
            Use with caution - this method will obliterate all present
            instances at the moment!

        :param extension:
            Extension to add.
        """
        if extension in self.extensions:
            return

        self.extensions.append(extension)
        self.create_db()

    @lru_cache(maxsize=32)
    def get_extension(self, extension):
        """Get an extension by name

        Returns None if the extension is not found.

        :param extension:
            Extension to retrieve by name
        """
        return self.db.get(extension)

    def remove_extension(self, extension):
        """Remove a given extension by name

        :param extension:
            Extension to remove.
        """
        extensions = list(self.extensions)
        for i, name in enumerate(e.__name__ for e in extensions):
            if name != extension:
                continue

            logger.debug("Removing extension: %s", name)
            del self.extensions[i]

            if name not in self.db:
                continue

            extension_inst = self.db.pop(name)
            self.events.unregister_callbacks_from_inst_all(extension_inst)

        result = len(extensions) > len(self.extensions)
        if result:
            self.get_extension.cache_clear()

        return result
