# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from collections import OrderedDict, deque
from functools import lru_cache
from logging import getLogger


_logger = getLogger(__name__)


class BaseExtension:

    """The base class for extensions.

    Any unknown attributes in this class are redirected to the ``base``
    attribute.

    """

    requires = []
    """Required extensions (must be a name)"""

    def __init__(self, base, **kwargs):
        """Initalise the BaseExtension instance.

        :param base:
            Base class for this method

        """
        self.base = base

    def __getattr__(self, attr):
        if attr.startswith('_'):
            # Private or internal state!
            raise AttributeError

        return getattr(self.base, attr)

