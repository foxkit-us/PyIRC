# Copyright © 2013-2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


""" Client to Client Protocol extensions and events """


from logging import getLogger

from PyIRC.extension import BaseExtension
from PyIRC.hook import hook
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
    """

    default_version = "Powered by PyIRC v{}".format(versionstr)
    """ Default CTCP version string to use """

    def __init__(self, base, **kwargs):
        """ Initalise the CTCP extension.

        Keyword arguments:

        ctcp_version
            Version string to use, defaults to default_version.
        """

        self.base = base

        self.version = kwargs.get("ctcp_version", self.default_version)

    @hook("hooks", "extension_post")
    def register_ctcp_hooks(self, event):
        """ Register CTCP hooks """

        events = self.base.events
        extensions = self.base.extensions

        events.register_class("hooks_ctcp", CTCPEvent)
        events.register_class("hooks_nctcp", CTCPEvent)
        extensions.create_hooks("hooks_ctcp", str.upper)
        extensions.create_hooks("hooks_nctcp", str.upper)

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

    @hook("commands", "PRIVMSG")
    def ctcp_in(self, event):
        """ Check message for CTCP (incoming) and dispatch if necessary. """

        ctcp = CTCPMessage.parse(event.line)
        if not ctcp:
            return

        command = ctcp.command
        self.call_event("hooks_ctcp", command, ctcp, event.line)

    @hook("commands", "NOTICE")
    def nctcp_in(self, event):
        """ Check message for NCTCP (incoming) and dispatch if necessary. """

        ctcp = CTCPMessage.parse(event.line)
        if not ctcp:
            return

        command = ctcp.command
        self.call_event("hooks_ctcp", command, ctcp, event.line)

    @hook("hooks_ctcp", "ping")
    def c_ping(self, event):
        """ Respond to CTCP ping """

        self.nctcp(event.ctcp.target, "PING", event.ctcp.param)

    @hook("hooks_ctcp", "version")
    def c_version(self, event):
        """ Respond to CTCP version """

        self.nctcp(event.ctcp.target, "VERSION", self.version)
