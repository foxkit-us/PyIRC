#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Extensions bundled with PyIRC.

These are the actual things that make PyIRC do things. They implement various
commands and allow new features to be easily added to the library in a
backwards-compatible way."""


from collections import UserDict
from importlib import import_module


__all__ = ["autojoin", "bantrack", "basetrack", "basicapi", "basicrfc", "cap",
           "channeltrack", "ctcp", "isupport", "kickrejoin", "lag", "sasl",
           "services", "starttls", "usertrack"]


class ExtensionsDatabase(UserDict):
    """A helper to late-bind extensions to avoid unnecessary imports and
    bloat"""

    # Default extensions and their requisite default modules
    _default_ext_mods = {
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
        "SASLPlain": "sasl",
        "ServicesLogin": "services",
        "StartTLS": "starttls",
        "UserTrack": "usertrack",
    }

    def lookup_module(self, extension):
        """Lookup a module for import"""
        module = self._default_ext_mods[extension]
        return import_module("PyIRC.extensions." + module)

    def __missing__(self, item):
        try:
            module = self.lookup_module(item)
        except KeyError:
            error = "No such module in the database: {}".format(item)
            raise KeyError(error) from e

        self.data[item] = getattr(module, item)
        return self.data[item]


base_recommended = ["AutoJoin", "BasicAPI", "BasicRFC", "CTCP", "ISupport"]
"""Basic recommended extensions that are compatible with most servers"""


ircv3_recommended = base_recommended + ["CapNegotiate", "SASLPlain",
                                        "StartTLS"]
"""Recommended extensions for use with IRCv3 compliant servers """


bot_recommended = ircv3_recommended + ["BanTrack", "ChannelTrack", "LagCheck",
                                       "ServicesLogin", "UserTrack"]
"""Recommended extensions for bots"""

