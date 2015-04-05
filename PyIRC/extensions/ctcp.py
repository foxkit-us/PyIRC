# Copyright © 2013 Andrew Wilcox.  All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.

""" CTCP extension.  Dispatches CTCP commands similar to IRC commands. """

import subprocess

try:
    import pkg_resources
except ImportError:
    pkg_resources = None

from collections import defaultdict
from logging import getLogger

from PyIRC.base import BaseExtension, EVENT_EXTENSION_POST
from PyIRC.numerics import Numerics


logger = getLogger(__name__)


def gitversion():
    command = ["git","log","-1","--pretty=format:%h"]
    return subprocess.check_output(command).decode()

try:
    _gitvers = gitversion()
except (OSError, subprocess.SubprocessError):
    _gitvers = "UNKNOWN"

try:
    _version = "PyIRC {}-{}".format(pkg_resources.require("PyIRC")[0].version,
                                    _gitvers)
except (pkg_resources.DistributionNotFound, IndexError, AttributeError,
        NameError):

    _version = "PyIRC Git {}".format(_gitvers)


class CTCPMessage:
    """ Represent a CTCP message. """

    __slots__ = ('line', 'command', 'target', 'param')

    def __init__(self, line, command, target, param):
        self.line = line
        self.command = command
        self.target = target
        self.param = param

    @classmethod
    def parse(cls, line):
        """ Return a new CTCPMessage from the line specified. """
        message = line.params[1]

        if not message.startswith("\x01") or not message.endswith("\x01"):
            return None

        message = message[1:-1]  # chop off \x01 at beginning and end
        (command, _, param) = message.partition(' ')

        return cls(line, command.upper(), line.hostmask.nick, param)


class CTCP(BaseExtension):
    """ Add CTCP dispatch functionaltiy. """

    def __init__(self, base, **kwargs):

        self.base = base

        self.commands = {
            "PRIVMSG" : self.ctcp_in,
            "NOTICE" : self.nctcp_in,
        }

        self.hooks = {
            EVENT_EXTENSION_POST : self.register_ctcp_hooks,
        }

        # Some default hooks
        self.commands_ctcp = {
            "ping" : self.c_ping,
            "version" : self.c_version,
        }

        self.version = kwargs.get("ctcp_version", _version)

        # Hooks for CTCP
        self.dispatch_ctcp = defaultdict(list)
        self.dispatch_nctcp = defaultdict(list)
    
    def register_ctcp_hooks(self):
        """ Register CTCP hooks """

        self.base.build_hooks(self.dispatch_ctcp, "implements_ctcp",
                              lambda s : s.lower())
        self.base.build_hooks(self.dispatch_nctcp, "implements_nctcp",
                              lambda s : s.lower())

    def ctcp(self, target, command, params=None):
        """ CTCP a target a given command """
        command = command.upper()
        if params:
            command = "{0} {1}".format(command, params)

        message = "\x01{0}\x01".format(command)
        self.send("PRIVMSG", [target, message])

    def nctcp(self, target, command, params=None):
        """ Reply to a CTCP """
        command = command.upper()
        if params:
            command = "{0} {1}".format(command, params)

        message = "\x01{0}\x01".format(command)
        self.send("NOTICE", [target, message])

    def ctcp_in(self, line):
        """ Check message for CTCP (incoming) and dispatch if necessary. """

        ctcp_msg = CTCPMessage.parse(line)
        if not ctcp_msg:
            return

        command = ctcp_msg.command.lower()
        self.dispatch_event(self.dispatch_ctcp, command, ctcp_msg)

    def nctcp_in(self, line):
        """ Check message for NCTCP (incoming) and dispatch if necessary. """

        ctcp_msg = CTCPMessage.parse(line)
        if not ctcp_msg:
            return

        command = ctcp_msg.command.lower()
        self.dispatch_event(self.dispatch_nctcp, command, ctcp_msg)

    def c_ping(self, message):
        """ Respond to CTCP ping """

        self.nctcp(message.target, "PING", message.param)

    def c_version(self, message):
        """ Respond to CTCP version """

        self.nctcp(message.target, "VERSION", self.version)
