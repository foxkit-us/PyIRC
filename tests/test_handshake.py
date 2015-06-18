# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Ensure proper handshake behaviour"""


import unittest

from PyIRC.extensions.basicrfc import BasicRFC
from PyIRC.io.null import NullSocket


class TestHandshakeBehaviour(unittest.TestCase):
    def setUp(self):
        self.username = 'TestUser'
        self.gecos = 'Test User'
        self.ns = NullSocket(serverport=(None, None), username=self.username,
                            nick='Test', gecos=self.gecos,
                            extensions=[BasicRFC])
        self.ns.connect()

    def test_user(self):
        line = self.ns.draw_line()
        while line:
            if line.command == 'USER':
                self.assertEquals(line.params[0], self.username,
                                  "Incorrect username")
                self.assertEquals(line.params[3], self.gecos,
                                  "Incorrect GECOS")
                return
            line = self.ns.draw_line()
        self.assertFalse(True, "No USER command received!")
