#!/usr/bin/env python3.4


import asyncio
from logging import basicConfig

from PyIRC.asyncio import IRCProtocol
from PyIRC.extensions import bot_recommended


basicConfig(level="DEBUG")

args = {
    'serverport' : ('irc.interlinked.me', 9999),
    'ssl' : True,
    'username' : 'Testbot',
    'nick' : 'Testbot',
    'gecos' : 'I am a test, pls ignore :)',
    'extensions' : bot_recommended,
    'sasl_username' : 'Testbot',
    'sasl_password' : 'loldongs123',
    'join' : ['#PyIRC'],
}

loop = asyncio.get_event_loop()

create = lambda : IRCProtocol(**args)
coro = loop.create_connection(create, *args['serverport'], ssl=args.get('ssl'))

loop.run_until_complete(coro)
loop.run_forever()
loop.close()
