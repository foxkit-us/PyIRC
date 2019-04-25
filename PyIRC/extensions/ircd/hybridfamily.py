# Copyright © 2015 A. Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""IRC daemon-specific routines for Hybrid derivatives.

This includes Charybdis and ircd-ratbox
"""

import re

from datetime import datetime
from logging import getLogger

from PyIRC.line import Hostmask
from PyIRC.signal import event
from PyIRC.numerics import Numerics
from PyIRC.extensions.ircd.base import (BaseServer, BanEntry, Extban,
                                        OperEntry, Uptime)

_logger = getLogger(__name__)


_stats_ban_re = re.compile(
    r"""^
    (?:
        # If there is a duration, this matches it.
        # Beware the space at the end of the line!
        Temporary\ (?P<type>.)-line\ (?P<duration>[0-9]+)\ min\.\ -\ 
    )?
    (?P<reason>.+?)
    (?:
        # Match the date and time of setting
        \ \(
            (?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})
            \ (?P<hour>[0-9]{2})\.(?P<minute>[0-9]{2})
        \)
    )?
    (?:
        # Operator reason (and setter)
        \|(?P<oreason>.+?)
        (?:
            # Setter format is (mask!of@setter{serv or nick})
            \ \(
                (?P<settermask>.+?)
                \{
                    (?P<setter>.+?)
                \}
            \)
        )?
    )?$""", re.X)


# NOTE: below is not used by charybdis!
_hybrid_oper_re = re.compile(
    r"""^
    \[
        (?P<flag>[AO])
    \]
    (?:
        # These may or may not occur, depending on if the oper is local or
        # global
        \[
            (?P<privs>.+?)
        \]
    )?
    \ (?P<nick>.+?)
    \ \((?P<user>.+?)@(?P<host>.+?)\)
    \ Idle: (?P<idle>[0-9]+)$
    """, re.X)


_charybdis_oper_re = re.compile(
    r"""^
    # Mind the trailing space!
    (?P<nick>.+?) \ 
    \(
        (?P<user>.+?)@(?P<host>.+?)
    \)$""", re.X)


_uptime_re = re.compile(
    r"""^
    # Mind the trailing space
    Server\ up\ (?P<days>[0-9]+)\ days,\ 
    (?P<hours>[0-9]{1,2}):
    (?P<minutes>[0-9]{1,2}):
    (?P<seconds>[0-9]{1,2})$
    """, re.X)


class HybridServer(BaseServer):

    """The ircd-hybrid provider."""

    requires = ["ISupport"]

    def provides(base):
        """Returns whether or not this extension can provide for the server."""
        version = base.basic_rfc.server_version[0]
        if version is None:
            return False

        if version.startswith("ircd-hybrid"):
            return True

        return False

    def generic_ban(self, ban, server, string, duration, reason):
        """Do a generic Hybrid-style ban.

        :param ban:
            Ban type to send.

        :param server:
            Server to send to.

        :param string:
            String to issue the ban with.

        :param duration:
            Duration of ban time in seconds.

        :param reason:
            The reason for the ban
        """
        params = []

        if duration:
            params.append(str(round(duration / 60)))

        if server:
            params.extend((string, "ON", server))
        else:
            params.append(string)

        if reason:
            params.append(reason)

        self.send(ban, params)

    def global_ban(self, user, duration, reason):
        """Ban a user on the IRC network. This is often referred to as a
        "g:line" or (confusingly) as a "k:line".

        :param user:
            A :py:class:`~PyIRC.extensions.usertrack.User` instance, a
            :py:class:`~PyIRC.line.Hostmask` instance, or a string, containing
            the mask or user to ban.

        :param duration:
            How long the ban should last in seconds, or ``None`` for permanent.

        :param reason:
            The reason for the ban.

        ..warning::
            This may have varying semantics based on IRC daemon. For example,
            on ircd-hybrid derivatives, this will be emulated as a global
            k:line, not as a g:line (which means something else entirely and
            is unlikely to be what you want outside of EFNet).

        ..note::
            This command requires IRC operator privileges, and may require
            additional privileges such as privsets or ACL's. Such documentation
            is out of scope for PyIRC. Check your IRC daemon's documentation,
            or consult a network administrator, for more information.
        """
        self.server_ban("*", user, duration, reason)

    def server_ban(self, server, user, duration, reason):
        """Ban a user on an IRC server. This is often referred to as a
        "k:line".

        :param server:
            The name of the server to apply the ban to. ``None`` sets it to
            the current server.

        :param user:
            A :py:class:`~PyIRC.extensions.usertrack.User` instance, a
            :py:class:`~PyIRC.line.Hostmask` instance, or a string, containing
            the mask or user to ban.

        :param duration:
            How long the ban should last in seconds, or ``None`` for permanent.

        :param reason:
            The reason for the ban.
        """
        if hasattr(user, "host"):
            user = "{}@{}".format(user.user, user.host)

        self.generic_ban("KLINE", server, user, duration, reason)

    def global_ip_ban(self, ip, duration, reason):
        """Ban an IP or CIDR range on the IRC network. This is often referred
        to as a "z:line" or (in hybrid derivatives) as a "d:line".

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
        self.server_ip_ban("*", ip, duration, reason)

    def server_ip_ban(self, server, ip, duration, reason):
        """Ban an IP or CIDR range on an IRC server. This is often referred to
        as a "z:line" or (in hybrid derivatives) as a "d:line".

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
        self.generic_ban("DLINE", server, ip, duration, reason)

    def global_nickchan_ban(self, string, duration, reason):
        """Ban a nick on the IRC network. This is often referred to as a
        "Q:line", "q:line", or (in hybrid derivatives) as a "resv".

        :param string:
            Nickname or channel to ban as a string.

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
        self.server_nickchan_ban("*", string, duration, reason)

    def server_nickchan_ban(self, server, string, duration, reason):
        """Ban a nick on an IRC server. This is often referred to as a
        "Q:line", "q:line", or (in hybrid derivatives) as a "resv".

        :param server:
            The name of the server to apply the ban to. ``None`` sets it to
            the current server.

        :param string:
            Nickname or channel to ban as a string.

        :param duration:
            How long the ban should last in seconds, or ``None`` for permanent.

        :param reason:
            The reason for the ban.

        ..warning::
            This is not supported on InspIRCd, as all q:lines are global.

        ..note::
            This command requires IRC operator privileges, and may require
            additional privileges such as privsets or ACL's. Such documentation
            is out of scope for PyIRC. Check your IRC daemon's documentation,
            or consult a network administrator, for more information.
        """
        self.generic_ban("RESV", server, string, duration, reason)

    def global_gecos_ban(self, string, duration, reason):
        """Ban a gecos on the IRC network. This is often referred to as an
        "sgline", "n:line", or (in hybrid derivatives) as an "x:line".

        :param string:
            GECOS to ban as a string.

        :param duration:
            How long the ban should last in seconds, or ``None`` for permanent.

        :param reason:
            The reason for the ban.

        ..warning::
            Not all servers support this. UnrealIRCd, notably, only supports
            permanent GECOS bans.

        ..note::
            This command requires IRC operator privileges, and may require
            additional privileges such as privsets or ACL's. Such documentation
            is out of scope for PyIRC. Check your IRC daemon's documentation,
            or consult a network administrator, for more information.
        """
        self.server_gecos_ban("*", string, duration, reason)

    def server_gecos_ban(self, server, string, duration, reason):
        """Ban a GECOS on an IRC server. This is often referred to as an
        "sgline", "n:line", or (in hybrid derivatives) as an "x:line".

        :param server:
            The name of the server to apply the ban to. ``None`` sets it to
            the current server.

        :param string:
            Nickname or channel to ban as a string.

        :param duration:
            How long the ban should last in seconds, or ``None`` for permanent.

        :param reason:
            The reason for the ban.

        ..warning::
            Not all servers support this. UnrealIRCd, notably, only supports
            permanent GECOS bans.

        ..note::
            This command requires IRC operator privileges, and may require
            additional privileges such as privsets or ACL's. Such documentation
            is out of scope for PyIRC. Check your IRC daemon's documentation,
            or consult a network administrator, for more information.
        """
        self.generic_ban("XLINE", server, string, duration, reason)

    def stats_global_ban(self):
        """Get a list of all global bans (often referred to as "g:lines" or,
        confusingly, as "k:lines").

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """
        self.stats_server_ban("*")

    def stats_server_ban(self, server):
        """Get a list of all server bans (often referred to as "k:lines").

        :param server:
            Server to get the list of bans on.

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """
        # Global
        self.send("STATS", ["G"])

        # k:lines, temp and permanent
        self.send("STATS", ["K", server])
        self.send("STATS", ["K", server])

    def stats_global_ip_ban(self):
        """Get a list of all global IP bans (often referred to as "z:lines" or
        "d:lines").

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """
        self.stats_server_ip_ban("*")

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
        self.send("STATS", ["d", server])
        self.send("STATS", ["D", server])

    def stats_global_nickchan_ban(self):
        """Get a list of all global nick/channel bans (often referred to as
        "Q:lines" or "resvs").

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """
        self.stats_server_nickchan_ban("*")

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
        self.send("STATS", ["r", server])
        self.send("STATS", ["R", server])

    def stats_global_gecos_ban(self):
        """Get a list of all global GECOS bans (often referred to as "sglines",
        "n:lines", or "x:lines").

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """
        self.stats_server_gecos_ban("*")

    def stats_server_gecos_ban(self, server):
        """Get a list of all server GECOS bans (often referred to as "sglines",
        "n:lines", or "x:lines).

        :param server:
            Server to get the list of bans on.

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """
        self.send("STATS", ["x", server])
        self.send("STATS", ["X", server])

    def stats_opers(self, server=None):
        """Get a list of IRC operators on the network. This may return either
        all the operators, or only the active ones, depending on the IRC
        daemon.

        :param server:
            Server to get the list of opers on. ``None`` defaults to the
            current server. This usually does not matter.

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """
        if server is not None:
            self.send("STATS", ["p", server])
        else:
            self.send("STATS", ["p"])

    def stats_uptime(self, server=None):
        """Get the uptime of the server.

        :param server:
            Server to get the uptime of. ``None`` defaults to the current server.
        """
        if server is not None:
            self.send("STATS", ["u", server])
        else:
            self.send("STATS", ["u"])

    @staticmethod
    def _parse_ban_lines(line):
        """Parse a foo:line in Hybrid-derived servers, excluding RESV and
        X:lines."""
        params = line.params

        match = _stats_ban_re.match(params[-1])
        assert match, "Bug in the stats matching regex!"

        t = match.group("type")
        if t == "K" or t == "G":
            # Don't use Hostmask, because this is for matching purposes.
            mask = (params[3], params[4], params[2])
        elif t == "D":
            mask = params[2]
        else:
            _logger.warning("Unknown bantype, just guessing!")
            mask = params[:-1]

        duration = int(match.group("duration")) * 60

        year = int(match.group("year"))
        month = int(match.group("month"))
        day = int(match.group("day"))
        hour = int(match.group("hour"))
        minute = int(match.group("minute"))
        if all(x is not None for x in (year, month, day)):
            setdate = datetime(year, month, day, hour, minute)
        else:
            setdate = None

        reason = match.group("reason")
        oreason = match.group("oreason")
        settermask = Hostmask.parse(match.group("settermask"))
        setter = match.group("setter")

        return BanEntry(mask, settermask, setter, setdate, duration, reason,
                        oreason)

    # pylint: disable=inconsistent-return-statements
    @event("commands", Numerics.RPL_STATSKLINE)
    @event("commands", Numerics.RPL_STATSDLINE)
    def parse_stats_ban(self, _, line):
        """Evaluate a stats line for a ban."""
        entry = self._parse_ban_lines(line)
        if not entry:
            return

        if line.command == Numerics.RPL_STATSKLINE.value():
            ban = "ban"
        else:
            ban = "ip_ban"

        return self.call_event("stats", ban, entry)

    @event("commands", Numerics.RPL_STATSQLINE)
    def parse_stats_user(self, _, line):
        """Evaluate a stats line for a RESV."""
        duration = line.params[1]
        mask = line.params[2]
        reason = line.params[3]

        entry = BanEntry(mask, None, None, None, duration, reason, None)
        return self.call_event("stats", "nickchan_ban", entry)

    @event("commands", Numerics.RPL_STATSXLINE)
    def parse_stats_gecos(self, _, line):
        """Evaluate a stats line for an X:line."""
        duration = line.params[1]
        mask = line.params[2]
        reason = line.params[3]

        entry = BanEntry(mask, None, None, None, duration, reason, None)
        return self.call_event("stats", "gecos_ban", entry)
    
    # pylint: disable=inconsistent-return-statements
    @event("commands", Numerics.RPL_STATSDEBUG)
    def parse_stats_opers(self, _, line):
        """Evaluate a stats line for an oper."""
        if line.params[1] != 'p':
            return

        match = _hybrid_oper_re(line.params[-1])
        if not match:
            return

        flag = match.group("flag")
        privs = match.group("privs")

        nick = match.group("nick")
        user = match.group("user")
        host = match.group("host")
        hostmask = Hostmask(nick=nick, user=user, host=host)

        idle = int(match.group("idle"))

        entry = OperEntry(flag, privs, hostmask, idle)
        return self.call_event("stats", "oper", entry)

    @event("commands", Numerics.RPL_STATSUPTIME)
    def parse_stats_uptime(self, _, line):
        """Evaluate the server uptime."""
        uptime = _uptime_re.match(line.params[-1])
        days = int(uptime.group("days"))
        hours = int(uptime.group("hours"))
        minutes = int(uptime.group("minutes"))
        seconds = int(uptime.group("seconds"))

        uptime = Uptime(days, hours, minutes, seconds)
        return self.call_event("stats", "uptime", uptime)


class RatboxServer(HybridServer):

    """The ircd-ratbox provider."""

    def provides(base):
        """Returns whether or not this extension can provide for the server."""
        version = base.basic_rfc.server_version[0]
        if version is None:
            return False

        if version.startswith("ircd-ratbox"):
            return True

        return False


class CharybdisServer(RatboxServer):

    """The Charybdis IRC daemon provider."""

    def provides(base):
        """Returns whether or not this extension can provide for the server."""
        version = base.basic_rfc.server_version[0]
        if version is None:
            return False

        if version.startswith("charybdis"):
            return True

        return False

    def extban_parse(self, string):
        if not string or string[0] != "$":
            return None

        negative = (string[1] == "~")
        if negative:
            ban = string[2]
            target = string[3:] if len(string) > 3 else None
        else:
            ban = string[1]
            target = string[2:] if len(string) > 2 else None

        isupport = self.base.isupport
        _, _, bans = isupport.get("EXTBAN").partition(",")

        if not ban in bans:
            _logger.warning("Unknown extban received: %s", string[1])

        return [Extban(negative, ban, target)]

    def stats_server_ban(self, server):
        """Get a list of all server bans (often referred to as "k:lines").

        :param server:
            Server to get the list of bans on.

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """
        # Global
        self.send("STATS", ["g"])

        # k:lines, temp and permanent
        self.send("STATS", ["K", server])
        self.send("STATS", ["K", server])

    # pylint: disable=inconsistent-return-statements
    @event("commands", Numerics.RPL_STATSDEBUG)
    def parse_stats_opers(self, _, line):
        """Evaluate a stats line for an oper."""
        if line.params[1] != 'p':
            return

        match = _charybdis_oper_re.match(line.params[-1])
        if not match:
            return

        nick = match.group("nick")
        user = match.group("user")
        host = match.group("host")
        hostmask = Hostmask(nick=nick, user=user, host=host)

        entry = OperEntry(None, None, hostmask, None)
        return self.call_event("stats", "oper", entry)


class IrcdSevenServer(CharybdisServer):

    """The ircd-seven provider."""

    def provides(base):
        """Returns whether or not this extension can provide for the server."""
        version = base.basic_rfc.server_version[0]
        if version is None:
            return False

        if version.startswith("ircd-seven"):
            return True

        return False
