#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Extensions bundled with PyIRC.

These are the actual things that make PyIRC do things. They implement various
commands and allow new features to be easily added to the library in a
backwards-compatible way.

The top-level module contains the :py:class:`~PyIRC.extensions.BaseExtension`
class (the parent of all extensions), various constants containing recommended
extensions for specific purposes, and internal machinery related to the event
subsystem.

"""


from importlib import import_module

from PyIRC.util.classutil import get_all_subclasses


__all__ = ["altnick", "autojoin", "bantrack", "basetrack", "basicapi",
           "basicrfc", "cap", "channeltrack", "ctcp", "isupport", "kickrejoin",
           "lag", "sasl", "services", "starttls", "usertrack"]


_builtin_extension_modules = {
    "AutoJoin": "autojoin",
    "BanTrack": "bantrack",
    "BaseTrack": "basetrack",
    "BasicAPI": "basicapi",
    "BasicRFC": "basicrfc",
    "CapNegotiate": "cap",
    "ChannelTrack": "channeltrack",
    "CTCP": "ctcp",
    "ISupport": "isupport",
    "KickRejoin": "kickrejoin",
    "LagCheck": "lag",
    "NumberSubstitueAlt": "altnick",
    "SASL": "sasl",
    "ServicesLogin": "services",
    "StartTLS": "starttls",
    "UserTrack": "usertrack",
    "UnderscoreAlt": "altnick",
}


def get_extension(name, prefer_builtin=True):
    """Get the class of a builtin extension by string.

    :returns:
        The extension class if found, else None.

    """

    # Attempt autodiscovery first
    extensions = [c for c in get_all_subclasses(BaseExtension) if
                  c.__name__ == name]

    if not extensions:
        # None found, try an import from the builtins.
        try:
            module_name = _builtin_extension_modules[name]
        except KeyError:
            return None

        # The below shouldn't fail, ever.
        module = import_module("PyIRC.extensions.%s" % module_name)
        return getattr(module, name)
    elif len(extensions) == 1:
        # We got only one. :p
        return extensions[0]
    else:
        extension_pref = None
        for extension in reversed(extensions):
            qualname = extension.__qualname__

            if (extension_pref is None or prefer_builtin is
                    qualname.startswith("PyIRC.extensions.")):
                # prefer_builtins controls the behaviour of this condition.
                # Yes, it's actually correct.
                extension_pref = extension

        return extension_pref


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

    def __setattr__(self, attr, value):
        if attr == 'base':
            return super().__setattr__(attr, value)

        try:
            getattr(self.base, attr)
        except AttributeError:
            return super().__setattr__(attr, value)
        else:
            return setattr(self.base, attr, value)


base_recommended = ["AutoJoin", "BasicAPI", "BasicRFC", "CTCP", "ISupport",
                    "UnderscoreAlt"]
"""Basic recommended extensions that are compatible with most servers"""


ircv3_recommended = base_recommended + ["CapNegotiate", "SASL", "StartTLS"]
"""Recommended extensions for use with IRCv3 compliant servers """


bot_recommended = ircv3_recommended + ["BanTrack", "ChannelTrack", "LagCheck",
                                       "ServicesLogin", "UserTrack"]
"""Recommended extensions for bots"""
