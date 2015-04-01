#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.

from collections import defaultdict
from operator import itemgetter

from numerics import Numerics
from line import Line


PRIORITY_DONTCARE = 0
PRIORITY_FIRST = -1
PRIORITY_LAST = 1

EVENT_OK = None  # default
EVENT_CANCEL = 1  # End processing
EVENT_TERMINATE_SOON = 2  # Disconnect
EVENT_TERMINATE_NOW = 3  # Quit


class BaseExtension:

    priority = PRIORITY_DONTCARE

    def __init__(self, base, **kwargs):
        self.base = base
    
        self.implements = {}


class BasicRFC(BaseExtension):
    """ Basic RFC1459 doodads """

    priority = PRIORITY_FIRST

    def __init__(self, base, **kwargs):
        self.base = base

        self.implements = {
            "NOTICE" : self.connected,
            "PING" : self.pong,
            Numerics.RPL_WELCOME : self.welcome,
        }

    def connected(self, line):
        self.base.connected = True

    def pong(self, line):
        self.base.send("PONG", line.params)

    def welcome(self, line):
        self.base.registered = True
    

class IRC:

    def __init__(self, server, port, user, nick, gecos, extensions, **kwargs):
        self.server = server
        self.port = port
        self.user = user
        self.nick = nick
        self.gecos = gecos
        self.extensions = list(extensions)

        self.kwargs = kwargs
        
        # Basic state
        self.connected = False
        self.registered = False
        
        self.build_dispatch_cache()

    def build_dispatch_cache(self):
        self.dispatch = defaultdict(list)
        self.extensions_inst = []

        for order, e in enumerate(self.extensions):
            extinst = e(self, **self.kwargs)

            self.extensions_inst.append(extinst)

            priority = extinst

            for command, callback in extinst.implements.items():
                if isinstance(command, Numerics):
                    command = command.value

                command = command.lower()

                self.dispatch[command].append([priority, order, callback])
                self.dispatch[command].sort()

    def recv(self, line):
        command = line.command.lower()

        fnlist = self.dispatch[command]
        if not fnlist:
            return

        for fn in fnlist:
            ret = fn[2](line)
            if ret == EVENT_CANCEL:
                return
            elif ret == EVENT_TERMINATE_SOON:
                self.send("QUIT", ["Plugin requested termination"])
                return
            elif ret == EVENT_TERMINATE_NOW:
                # FIXME - maybe should raise?
                quit()

    def send(self, command, params):
       line = Line(command=command, params=params)
