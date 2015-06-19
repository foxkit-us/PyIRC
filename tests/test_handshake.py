# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Ensure proper handshake behaviour"""


import unittest

from test_helpers import new_connection


class TestHandshakeBehaviour(unittest.TestCase):
    def test_user(self):
        ns = new_connection(username='TestUser', gecos='Test User')
        line = ns.draw_line()
        while line:
            if line.command == 'USER':
                self.assertEqual(line.params[0], 'TestUser',
                                 "Incorrect username")
                self.assertEqual(line.params[3], 'Test User',
                                 "Incorrect GECOS")
                return
            line = ns.draw_line()
        self.assertFalse(True, "No USER command received!")

    def test_invalid_user(self):
        with self.assertRaises(ValueError, msg="Invalid username accepted!"):
            ns = new_connection(username='This should not work')

    def test_nick(self):
        nick = 'Tester'
        ns = new_connection(nick=nick)
        line = ns.draw_line()
        while line:
            if line.command == 'NICK':
                self.assertEqual(line.params[0], nick, "Incorrect nickname")
                return
            line = ns.draw_line()
        self.assertFalse(True, "No NICK command received!")
