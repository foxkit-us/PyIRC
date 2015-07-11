# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from collections import OrderedDict, deque
from functools import lru_cache
from logging import getLogger

from PyIRC.extensions import ExtensionsDatabase


_logger = getLogger(__name__)


class BaseExtension:

    """The base class for extensions.

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
        if attr.endswith('_hooks') or attr.startswith('_'):
            # Private or internal state!
            raise AttributeError

        return getattr(self.base, attr)


class ExtensionManager:

    """Manage extensions to PyIRC's library, and register their hooks."""

    def __init__(self, base, kwargs, extensions=(), database=None):
        """Initialise the extensions manager.

        :param base:
            Base instance to pass to each extension.

        :param kwargs:
            Keyword arguments to pass to each extension.

        :param extensions:
            Initial list of extensions.

        :param database:
            Optional extensions database to use.

        """

        self.base = base
        self.kwargs = kwargs

        if database is not None:
            self.default_db = database
        else:
            self.default_db = ExtensionsDatabase()

        # Serialise the extensions list into real extensions classes
        # Strings are looked up in the extensions database
        self.extensions = [self.default_db[e] if isinstance(e, str) else e
                           for e in extensions]

        self.db = OrderedDict()

    def create_db(self):
        """Build the extensions database."""
        self.db.clear()
        self.get_extension.cache_clear()

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

    def add_extension(self, extension):
        """Add an extension by class.

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
        """Get an extension by name.

        Returns None if the extension is not found.

        :param extension:
            Extension to retrieve by name

        """
        return self.db.get(extension)

    def remove_extension(self, extension):
        """Remove a given extension by name.

        :param extension:
            Extension to remove.

        """
        extensions = list(self.extensions)
        for i, name in enumerate(e.__name__ for e in extensions):
            if name != extension:
                continue

            _logger.debug("Removing extension: %s", name)
            del self.extensions[i]

            if name not in self.db:
                continue

            extension_inst = self.db.pop(name)

            # FIXME TODO - iterate all members and purge Slots.

        result = len(extensions) > len(self.extensions)
        if result:
            self.get_extension.cache_clear()

        return result
