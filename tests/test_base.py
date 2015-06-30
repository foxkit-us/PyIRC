#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Exercise the base modules a bit."""


import unittest
import doctest

from PyIRC import *


# These have doctests
def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(auxparse))
    tests.addTests(doctest.DocTestSuite(line))
    tests.addTests(doctest.DocTestSuite(casemapping))
    return tests
