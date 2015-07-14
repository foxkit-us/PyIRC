#!/usr/bin/env python3.4


import asyncio
import ssl
import signal

from random import choice
from logging import basicConfig

from PyIRC.signal import event
from PyIRC.io.asyncio import IRCProtocol
from PyIRC.extensions import bot_recommended


class TestProtocol(IRCProtocol):
    """Some furry bollocks test class."""

    yifflines = (
        "rrf~",
        "oh yes~",
        "do more~",
        "right there~",
        "mmmm yes~",
        "oh yeah~",
    )

    flirtlines = (
        "not in here! message me",
        "oh I couldn't in public...",
        "do I look like silverwoof to you?"
        "come on, there's people here!",
        "I don't do it in channels, sorry...",
    )

    @event("commands", "PRIVMSG")
    def respond(self, event):
        line = event.line
        params = line.params

        if len(params) < 2:
            return

        if self.casecmp(self.basic_rfc.nick, params[0]):
            params = [line.hostmask.nick, choice(self.yifflines)]
        else:
            # Ensure it starts with us
            check_self = params[-1][:len(self.basic_rfc.nick)]
            if not self.casecmp(self.basic_rfc.nick, check_self):
                return

            params = [params[0], choice(self.flirtlines)]

        self.send("PRIVMSG", params)

basicConfig(level="DEBUG")

args = {
    'serverport': ('irc.interlinked.me', 6667),
    'ssl': False,
    'username': 'Testbot',
    'nick': 'Testbot',
    'gecos': 'I am a test, pls ignore :)',
    'extensions': bot_recommended,
    'sasl_username': 'Testbot',
    'sasl_password': 'loldongs123',
    'join': ['#PyIRC'],
}


def sigint(*protos):
    for proto in protos:
        try:
            proto.send("QUIT", ["Terminating due to ctrl-c!"])
            proto.close()
        except Exception as e:
            # Ugh! A race probably happened. Yay, signals.
            pass

    print()
    print("Terminating due to ctrl-c!")

    quit()


inst = TestProtocol(**args)
coro = inst.connect()

loop = asyncio.get_event_loop()
loop.add_signal_handler(signal.SIGINT, sigint, inst)

try:
    loop.run_until_complete(coro)
    loop.run_forever()
finally:
    loop.close()
