# Copyright © 2015 A. Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Utilities for class metaprogramming and related purposes."""


def get_all_subclasses(cls):
    """Generator for all subclasses for a given class."""
    for subclass in cls.__subclasses__():
        yield subclass
        yield from get_all_subclasses(subclass)
