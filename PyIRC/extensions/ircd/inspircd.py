# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""IRC daemon-specific routines for InspIRCd 2.x.

This extension has not been tested on InspIRCd 1.2.  It requires 2.0, but has
been tested on 2.2 (development) as well.

"""

from logging import getLogger
import re

from PyIRC.extensions.ircd.base import BaseServer
from PyIRC.numerics import Numerics
from PyIRC.signal import event


_logger = getLogger(__name__)


ban_regex = re.compile('^(\d+y)?(\d+w)?(\d+d)?(\d+h)?(\d+m)?(\d+s)?$')


class InspIRCdServer(BaseServer):

    """InspIRCd server-specific extension provider."""

    def provides(base):
        """Returns whether or not this extension can provide for the
        server."""
        version = base.basic_rfc.server_version[0]
        if version is None or not version.startswith("InspIRCd-2"):
            return False
        else:
            return True

    def extban_parse(self, string):
        """Parse an extban.

        :param string:
            String to parse

        :returns:
            An :py:class:`~PyIRC.extensions.ircd.Extban` instance.
        """
        raise NotImplementedError("Extbans are not supported yes.")

    def _abstract_ban(self, ban_type, mask, duration, reason):
        """Perform an oper ban.  This is NOT a normal channel ban.

        :param str ban_type:
            The type of ban (KLINE, ZLINE, QLINE, GLINE, ELINE).  This is case
            insensitive (and will always be upper-cased).

        :param str mask:
            The ban type-appropriate mask to ban (user@host, nick, IP, etc).

        :param duration:
            The duration of the ban, either in seconds (including an int), or
            in Fancy Dumb Ban Duration Format (.y.w.d.h.m.s).  ``None`` will be
            considered permanent, as will 0.

        :param str reason:
            The reason for the ban.  Make it a good one!

        :returns:
            Nothing.

        :raises ValueError:
            If duration is not properly specified.
        """

        if duration is None:
            duration = '0'
        elif isinstance(duration, int):
            duration = str(duration)
        # if it is an int (seconds), we don't need to do anything
        elif not duration.isnumeric():
            if ban_regex.match(duration) is None:
                error = "Invalid duration '{}' specified".format(duration)
                raise ValueError(error)

        self.send(ban_type.upper(), [str(mask), duration, reason])

    def global_ban(self, user, duration, reason):
        """Ban a user on the IRC network. This is often referred to as a
        "g:line".

        :param user:
            A :py:class:`~PyIRC.extensions.usertrack.User` instance, a
            :py:class:`~PyIRC.line.Hostmask` instance, or a string, containing
            the mask or user to ban.

        :param duration:
            How long the ban should last in seconds, or ``None`` for permanent.

        :param reason:
            The reason for the ban.

        ..note::
            This command requires IRC operator privileges, and may require
            additional privileges such as privsets or ACL's. Such documentation
            is out of scope for PyIRC. Check your IRC daemon's documentation,
            or consult a network administrator, for more information.
        """

        self._abstract_ban('GLINE', user, duration, reason)

    def server_ban(self, server, user, duration, reason):
        """Ban a user on an IRC server. This is often referred to as a
        "k:line".

        :param server:
            The name of the server to apply the ban to.  Note that InspIRCd does
            not support remotely setting k:lines so this parameter is ignored.

        :param user:
            A :py:class:`~PyIRC.extensions.usertrack.User` instance, a
            :py:class:`~PyIRC.line.Hostmask` instance, or a string, containing
            the mask or user to ban.

        :param duration:
            How long the ban should last in seconds, or ``None`` for permanent.

        :param reason:
            The reason for the ban.
        """

        self._abstract_ban('KLINE', user, duration, reason)

    def global_ip_ban(self, ip, duration, reason):
        """Ban an IP or CIDR range on the IRC network. This is often referred
        to as a "z:line".

        :param ip:
            A string containing the IP or CIDR to ban.

        :param duration:
            How long the ban should last in seconds, or ``None`` for permanent.

        :param reason:
            The reason for the ban.

        ..note::
            This command requires IRC operator privileges, and may require
            additional privileges such as privsets or ACL's. Such documentation
            is out of scope for PyIRC. Check your IRC daemon's documentation,
            or consult a network administrator, for more information.
        """

        self._abstract_ban('ZLINE', ip, duration, reason)

    def server_ip_ban(self, server, ip, duration, reason):
        """Ban an IP or CIDR range on an IRC server. This is often referred to
        in hybrid derivatives as a "d:line".

        :param server:
            The name of the server to apply the ban to. ``None`` sets it to
            the current server.

        :param ip:
            A string containing the IP or CIDR to ban.

        :param duration:
            How long the ban should last in seconds, or ``None`` for permanent.

        :param reason:
            The reason for the ban.

        ..note::
            This command requires IRC operator privileges, and may require
            additional privileges such as privsets or ACL's. Such documentation
            is out of scope for PyIRC. Check your IRC daemon's documentation,
            or consult a network administrator, for more information.
        """

        # InspIRCd doesn't have a "d:line", but SaberUK did point out that
        # a local k:line set to *@{ip or mask} is equivalent since InspIRCd
        # checks *@ip k:lines before checks (just like charybdis does with d:).
        self._abstract_ban('KLINE', '*@{}'.format(ip), duration, reason)

    def global_nickchan_ban(self, string, duration, reason):
        """Ban a nick on the IRC network. This is often referred to as a
        "q:line".

        :param string:
            Nickname to ban as a string.

        :param duration:
            How long the ban should last in seconds, or ``None`` for permanent.

        :param reason:
            The reason for the ban.

        ..note::
            This command requires IRC operator privileges, and may require
            additional privileges such as privsets or ACL's. Such documentation
            is out of scope for PyIRC. Check your IRC daemon's documentation,
            or consult a network administrator, for more information.
        """

        self._abstract_ban('QLINE', string, duration, reason)

    def server_nickchan_ban(self, server, string, duration, reason):
        """Ban a nick on an IRC server. This is often referred to as a
        "Q:line", "q:line", or (in hybrid derivatives) as a "resv".

        ..warning::
            This is not supported on InspIRCd, as all q:lines are global.
        """

        raise NotImplementedError('InspIRCd does not support server q:lines.')

    # for global_gecos_ban, there is R:line.  however, its syntax can vary
    # widely based on the loaded regex module (glob, pcre, posix, C++11)...
    # we COULD parse /MODULES to see the loaded regex module and try to set an
    # R:line that way, but meh.  I don't think it's worth it.

    def stats_global_ban(self):
        """Get a list of all global bans (often referred to as "g:lines").

        ..note::
            This may be restricted or even filtered. Unless you are an operator,
            take the information that is returned with a grain of salt.
        """

        self.send('STATS', ['g'])

    def stats_server_ban(self, server):
        """Get a list of all server bans (often referred to as "k:lines").

        :param server:
            Server to get the list of bans on.

        ..note::
            This may be restricted or even filtered. Unless you are an operator,
            take the information that is returned with a grain of salt.
        """

        if server is not None:
            self.send('STATS', ['k', server])
        else:
            self.send('STATS', ['k'])

    def stats_global_ip_ban(self):
        """Get a list of all global IP bans (often referred to as "z:lines").

        ..note::
            This may be restricted or even filtered. Unless you are an operator,
            take the information that is returned with a grain of salt.
        """

        self.send('STATS', ['Z'])

    def stats_server_ip_ban(self, server):
        """Get a list of all server IP bans (often referred to as "z:lines" or
        "d:lines").

        :param server:
            Server to get the list of bans on.

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """

        self.stats_server_ban(server)

    def stats_global_nickchan_ban(self):
        """Get a list of all global nick/channel bans (often referred to as
        "Q:lines" or "resvs").

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """

        self.send('STATS', 'q')

    def stats_server_nickchan_ban(self, server):
        """Get a list of all server nick/channel bans (often referred to as
        "Q:lines", "q:lines" or "resvs").

        :param server:
            Server to get the list of bans on.

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """

        raise NotImplementedError('InspIRCd does not support server q:lines.')

    # ---
    # we have no global/server gecos_bans as described in earlier block comment.
    # ---

    def stats_opers(self, server=None):
        """Get a list of IRC operators on the network. This may return either
        all the operators, or only the active ones, depending on the IRC
        daemon.

        :param server:
            Server to get the list of opers on. ``None`` defaults to the
            current server. This usually does not matter.

        ..note::
            This may be restricted or even filtered. Unless you are an operator,
            take the information that is returned with a grain of salt.
        """

        if server is not None:
            self.send('STATS', ['P', server])
        else:
            self.send('STATS', ['P'])

    def stats_uptime(self, server=None):
        """Get the uptime of the server.

        :param server:
            Server to get the uptime of. ``None`` defaults to the current
            server.
        """

        if server is not None:
            self.send('STATS', ['u', server])
        else:
            self.send('STATS', ['u'])
