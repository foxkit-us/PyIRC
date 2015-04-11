# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


""" Utilities for class metaprogramming and related purposes """


def private_mangle(cls, name):
    """ Generate a private name based on the given name """
    if not name.startswith('__'):
        return name

    name_mangle = '_{}__'.format(cls.__name__)
    return name.replace('__', name_mangle, 1)

