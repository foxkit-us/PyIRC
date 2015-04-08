# Copyright © 2013 Andrew Wilcox.  All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.

""" CTCP extension.  Dispatches CTCP commands similar to IRC commands. """

from logging import getLogger

from PyIRC.extension import BaseExtension
from PyIRC.event import EventState, LineEvent
from PyIRC.numerics import Numerics
from PyIRC.util.version import versionstr


logger = getLogger(__name__)


class CTCPEvent(LineEvent):
    """ A CTCP event """

    def __init__(self, event, ctcp, line):
        super().__init__(event, line)
        self.ctcp = ctcp


class CTCPMessage:
    """ Represent a CTCP message. """

    __slots__ = ('line', 'command', 'target', 'param')

    def __init__(self, command, target, param):
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

        return cls(command.upper(), line.hostmask.nick, param)


class CTCP(BaseExtension):
    """ Add CTCP dispatch functionaltiy.

    Hooks may be added by having a commands_ctcp or commands_nctcp mapping in
    your base class.

    ctcp_version
        Default CTCP version string to use.
    """

    def __init__(self, base, **kwargs):


        self.base = base

        self.commands = {
            "PRIVMSG" : self.ctcp_in,
            "NOTICE" : self.nctcp_in,
        }

        self.hooks = {
            "extension_post" : self.register_ctcp_hooks,
        }

        # Some default hooks
        self.commands_ctcp = {
            "ping" : self.c_ping,
            "version" : self.c_version,
        }

        self.version = kwargs.get("ctcp_version", versionstr)

    def register_ctcp_hooks(self, event):
        """ Register CTCP hooks """

        self.base.events.register_class("hooks_ctcp", CTCPEvent)
        self.base.build_hooks("hooks_ctcp", "commands_ctcp", str.upper)
        self.base.build_hooks("hooks_ctcp", "commands_nctcp", str.upper)

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

    def ctcp_in(self, event):
        """ Check message for CTCP (incoming) and dispatch if necessary. """

        ctcp = CTCPMessage.parse(event.line)
        if not ctcp:
            return

        command = ctcp.command
        self.call_event("hooks_ctcp", command, ctcp, event.line)

    def nctcp_in(self, event):
        """ Check message for NCTCP (incoming) and dispatch if necessary. """

        ctcp = CTCPMessage.parse(event.line)
        if not ctcp:
            return

        command = ctcp.command
        self.call_event("hooks_ctcp", command, ctcp, event.line)

    def c_ping(self, event):
        """ Respond to CTCP ping """

        self.nctcp(event.ctcp.target, "PING", event.ctcp.param)

    def c_version(self, event):
        """ Respond to CTCP version """

        self.nctcp(event.ctcp.target, "VERSION", self.version)
