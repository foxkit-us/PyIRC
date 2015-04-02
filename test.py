#!/usr/bin/env python3.4

import socket
from logging import basicConfig

from ircsocket import IRCSocket
from base import BasicRFC
from extensions.isupport import ISupport
from extensions.autojoin import Autojoin

basicConfig(level="INFO")

arguments = {
    'serverport' : ('irc.interlinked.me', 9999),
    'ssl' : True,
    'user' : 'Testbot',
    'nick' : 'Testbot',
    'gecos' : 'I am a test, pls ignore :)',
    'extensions' : [BasicRFC, ISupport, Autojoin],
    'join' : ['#PyIRC'],
}

i = IRCSocket(**arguments)
i.loop()
