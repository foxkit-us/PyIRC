#!/usr/bin/env python3.4


import asyncio, ssl

from random import choice
from logging import basicConfig

from PyIRC.io.asyncio import IRCProtocol
from PyIRC.hook import hook
from PyIRC.extensions import bot_recommended


class TestProtocol(IRCProtocol):
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

    @hook("commands", "PRIVMSG")
    def respond(self, event):
        line = event.line
        params = line.params
        target = params[0]
        if (target != self.nick and params[-1].startswith(self.nick)):
            self.send("PRIVMSG", [target, choice(self.flirtlines)])
            return

        hostmask = line.hostmask
        if not (hostmask and hostmask.nick):
            return

        self.send("PRIVMSG", [hostmask.nick, choice(self.yifflines)])


basicConfig(level="DEBUG")

args = {
    'serverport' : ('irc.interlinked.me', 6667),
    'ssl' : False,
    'username' : 'Testbot',
    'nick' : 'Testbot',
    'gecos' : 'I am a test, pls ignore :)',
    'extensions' : bot_recommended,
    'sasl_username' : 'Testbot',
    'sasl_password' : 'loldongs123',
    'join' : ['#PyIRC'],
}

inst = TestProtocol(**args)

loop = asyncio.get_event_loop()
loop.run_until_complete(inst.connect())
loop.run_forever()
loop.close()
