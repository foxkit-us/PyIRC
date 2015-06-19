# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Common helper methods for unit tests."""

from PyIRC.extensions.basicrfc import BasicRFC
from PyIRC.io.null import NullSocket
from PyIRC.line import Line


def new_connection(username='TestUser', nick='Test', gecos='Test User',
                   extensions=[BasicRFC]):
    ns = NullSocket(serverport=(None, None), username=username, nick=nick,
                    gecos=gecos, extensions=extensions)
    ns.connect()
    return ns

def new_conn_with_handshake(username='TestUser', nick='Test', gecos='Test User',
                            extensions=[BasicRFC]):
    ns = new_connection(username, nick, gecos, extensions)
    ns.draw_line()  # the USER
    ns.draw_line()  # and the NICK
    ns.inject_line(Line(command='001',
                        params=(nick, 'Welcome to the test network %s' % nick)))
    ns.inject_line(Line(command='002',
                        params=(nick, 'Your host is a.non-existent.test.server')))
    return ns
