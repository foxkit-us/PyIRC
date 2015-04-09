# Copyright © 2013-2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


""" CTCP extension.  Dispatches CTCP commands similar to IRC commands. """


from logging import getLogger

from PyIRC.extension import BaseExtension
from PyIRC.event import EventState, LineEvent
from PyIRC.numerics import Numerics
from PyIRC.auxparse import CTCPMessage
from PyIRC.util.version import versionstr


logger = getLogger(__name__)


class CTCPEvent(LineEvent):
    """ A CTCP event """

    def __init__(self, event, ctcp, line):
        super().__init__(event, line)
        self.ctcp = ctcp


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

        default_version = "Powered by PyIRC v{}".format(versionstr)
        self.version = kwargs.get("ctcp_version", default_version)

    def register_ctcp_hooks(self, event):
        """ Register CTCP hooks """

        self.base.events.register_class("hooks_ctcp", CTCPEvent)
        self.base.build_hooks("hooks_ctcp", "commands_ctcp", str.upper)
        self.base.build_hooks("hooks_ctcp", "commands_nctcp", str.upper)

    def ctcp(self, target, command, param=None):
        """ CTCP a target a given command """

        ctcp = CTCPMessage("PRIVMSG", command.upper(), param)
        line = ctcp.line()

        self.send(line.command, line.params)

    def nctcp(self, target, command, param=None):
        """ Reply to a CTCP """
        
        ctcp = CTCPMessage("NOTICE", command.upper(), param)
        line = ctcp.line()

        self.send(line.command, line.params)

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
