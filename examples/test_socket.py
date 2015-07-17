#!/usr/bin/env python3.4

from logging import basicConfig

from PyIRC.io.socket import IRCSocket
from PyIRC.extensions import bot_recommended


basicConfig(level="DEBUG")

arguments = {
    'serverport': ('irc.interlinked.me', 9999),
    'ssl': True,
    'username': 'Testbot',
    'nick': 'Testbot',
    'gecos': 'I am a test, pls ignore :)',
    'extensions': bot_recommended,
    'sasl_username': 'Testbot',
    'sasl_password': 'loldongs123',
    'join': ['#PyIRC'],
}

i = IRCSocket(**arguments)
i.loop()
