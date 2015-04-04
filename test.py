#!/usr/bin/env python3.4

from logging import basicConfig

from PyIRC.socket import IRCSocket
from PyIRC.base import BasicRFC
from PyIRC.extensions.isupport import ISupport
from PyIRC.extensions.autojoin import Autojoin
from PyIRC.extensions.cap import CapNegotiate
from PyIRC.extensions.starttls import STARTTLS
from PyIRC.extensions.sasl import SASLPlain

basicConfig(level="DEBUG")

arguments = {
    'serverport' : ('irc.interlinked.me', 9999),
    'ssl' : True,
    'user' : 'Testbot',
    'nick' : 'Testbot',
    'gecos' : 'I am a test, pls ignore :)',
    'extensions' : [BasicRFC, ISupport, Autojoin, CapNegotiate, SASLPlain, STARTTLS],
    'sasl_username' : 'Testbot',
    'sasl_password' : 'loldongs123',
    'join' : ['#PyIRC'],
}

i = IRCSocket(**arguments)
i.loop()
