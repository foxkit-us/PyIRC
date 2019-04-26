#!/usr/bin/env python3

from IPython.core import ultratb
from IPython.terminal.embed import InteractiveShellEmbed
from logging import basicConfig
import sys

from PyIRC.signal import event
from PyIRC.io.socket import IRCSocket
from PyIRC.extensions import bot_recommended


basicConfig(level="DEBUG")

sys.excepthook = ultratb.FormattedTB(mode='Verbose', call_pdb=1)

arguments = {
    'serverport': ('irc.interlinked.me', 9999),
    'ssl': True,
    'username': 'Testbot',
    'nick': 'IPythonBot',
    'gecos': 'I am a test, pls ignore :)',
    'extensions': bot_recommended,
    'sasl_username': 'Testbot',
    'sasl_password': 'loldongs123',
    'join': ['#PyIRC'],
}

pyshell = InteractiveShellEmbed(
    banner1='Starting a shell. Remember to PONG or resume before you ping out!',
    exit_msg='Returning to IRC message pump.')


class IPythonExampleBot(IRCSocket):

    @event("commands", "PRIVMSG")
    def on_msg(self, event):
        msg = event.line.params[-1]
        if msg == '>>> shell':
            pyshell("Dropping to shell on request.")


i = IPythonExampleBot(**arguments)
i.loop()
