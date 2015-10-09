# Copyright © 2013-2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Client to Client Protocol extensions and events."""


from logging import getLogger


from PyIRC.signal import event
from PyIRC.extensions import BaseExtension
from PyIRC.auxparse import CTCPMessage
from PyIRC.util.version import versionstr


_logger = getLogger(__name__)  # pylint: disable=invalid-name


class CTCP(BaseExtension):

    """Add CTCP dispatch functionaltiy.

    Hooks may be added by having a commands_ctcp or commands_nctcp
    mapping in your base class.

    """

    default_version = "Powered by PyIRC v{}".format(versionstr)
    """ Default CTCP version string to use """

    def __init__(self, *args, **kwargs):
        """Initalise the CTCP extension.

        :key ctcp_version:
            Version string to use, defaults to default_version.

        """
        super().__init__(*args, **kwargs)

        self.version = kwargs.get("ctcp_version", self.default_version)

    def ctcp(self, target, command, param=None):
        """CTCP a target a given command."""
        ctcp = CTCPMessage("PRIVMSG", command.upper(), target, param)
        line = ctcp.line

        self.send(line.command, line.params)

    def nctcp(self, target, command, param=None):
        """Reply to a CTCP."""
        ctcp = CTCPMessage("NOTICE", command.upper(), target, param)
        line = ctcp.line

        self.send(line.command, line.params)

    @event("commands", "PRIVMSG")
    def ctcp_in(self, _, line):
        """Check message for CTCP (incoming) and dispatch if necessary."""
        ctcp = CTCPMessage.parse(line)
        if not ctcp:
            return

        command = ctcp.command
        self.call_event("commands_ctcp", command, ctcp, line)

    @event("commands", "NOTICE")
    def nctcp_in(self, _, line):
        """Check message for NCTCP (incoming) and dispatch if necessary."""
        ctcp = CTCPMessage.parse(line)
        if not ctcp:
            return

        command = ctcp.command
        self.call_event("commands_ctcp", command, ctcp, line)

    @event("commands_ctcp", "PING")
    def c_ping(self, _, ctcp, line):
        """Respond to CTCP ping."""
        self.nctcp(ctcp.target, "PING", ctcp.param)

    @event("commands_ctcp", "VERSION")
    def c_version(self, _, ctcp, line):
        """Respond to CTCP version."""
        self.nctcp(ctcp.target, "VERSION", self.version)
