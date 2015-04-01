#!/usr/bin/env python3.4

import socket

from ircsocket import IRCSocket
from base import BasicRFC
from logging import basicConfig

basicConfig(level="INFO")
i = IRCSocket(('irc.interlinked.me', 6667), 'Elizabeth', 'Testbot', 'I am a test, pls ignore', extensions=[BasicRFC], family=socket.AF_INET)
i.loop()
