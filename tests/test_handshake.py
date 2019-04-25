# Copyright © 2015 A. Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Ensure proper handshake behaviour."""


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

#    not implemented yet.
#    def test_invalid_user(self):
#        with self.assertRaises(ValueError, msg="Invalid username accepted!"):
#            ns = new_connection(username='This should not work')

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

    def test_pass(self):
        # this test password is inspired by ZNC, if anyone's wondering.
        password = 'password/with:symbols and such'
        ns = new_connection(server_password=password)
        line = ns.draw_line()
        self.assertEqual(line.command, 'PASS', "PASS must be sent first")
        self.assertEqual(line.params[0], password, "Passwords don't match")

    def test_nick_before_user(self):
        # RFC 1459, §4.1, pp. 13-14
        # The recommended order for a client to register is as follows:
        # 1. Pass message
        # 2. Nick message
        # 3. User message
        ns = new_connection()
        line = ns.draw_line()
        self.assertEqual(line.command, 'NICK', "NICK must be sent first")
        line = ns.draw_line()
        self.assertEqual(line.command, 'USER', "USER must be send after NICK")
