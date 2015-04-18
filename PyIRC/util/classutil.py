# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


""" Utilities for class metaprogramming and related purposes """


def private_mangle(cls, name):
    """Generate a private name based on the given name

    :param cls:
        Class (instance or not) to use for the mangling
    :param name:
        Name to mangle.
    """
    if not name.startswith('__'):
        return name

    cls_name = getattr(cls, '__name__', cls.__class__.__name__)
    name_mangle = '_{}__'.format(cls_name)
    return name.replace('__', name_mangle, 1)
