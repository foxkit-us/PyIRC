# Copyright © 2013-2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Track users we have seen and their associated data.

Tracks users we know about, whether on channels or through private
messages. Maintains state such as nicknames, channel statuses, away
status, and the like.

"""


from itertools import chain
from random import randint
from functools import partial
from logging import getLogger


from PyIRC.signal import event
from PyIRC.auxparse import (prefix_parse, who_flag_parse, status_prefix_parse,
                            userhost_parse)
from PyIRC.casemapping import IRCDict, IRCDefaultDict, IRCSet
from PyIRC.extensions import BaseExtension
from PyIRC.line import Hostmask
from PyIRC.numerics import Numerics


_logger = getLogger(__name__)  # pylint: disable=invalid-name


class User:

    """A user entity.

    :ivar channels:
        Mapping of channels, where the keys are casemapped channel names, and
        the values are their status modes on the channel.

    For more elaborate channel tracking, see
    :py:module:`~PyIRC.extensions.channeltrack`.

    """

    def __init__(self, case, nick, **kwargs):
        """Store the data for a user.

        Unknown values are stored as None, whereas empty ones are stored as
        '' or 0, so take care in comparisons involving values from this class.

        :param nick:
            Nickname of the user, not casemapped.

        :param case:
            Casemapping to use for channels member.

        :key username:
            Username of the user, or ident (depending on IRC daemon).

        :key host:
            Hostname of the user. May be fake due to a cloak.

        :key gecos:
            The GECOS (aka "real name") of a user. Usually just freeform data
            of dubious usefulness.

        :key account:
            Services account name of the user.

        :key server:
            Server the user is on. Not always reliable or present.

        :key secure:
            User is using SSL. Always assume unsecured unless set to True.

        :key operator:
            User is an operator. Being set to None does not guarantee a user
            is not an operator due to IRC daemon limitations and data hiding.

        :key signon:
            Signon time for the user. May not be set.

        :key ip:
            IP for the user reported from the server. May be bogus and likely
            nonexistent on networks with host cloaking.

        :key realhost:
            Real hostname for a user. Probably not present in most cases.

        """
        if nick is None:
            raise ValueError("nick may not be None")

        self.nick = nick
        self.username = kwargs.get("username", None)
        self.host = kwargs.get("host", None)
        self.gecos = kwargs.get("gecos", None)
        self.account = kwargs.get("account", None)
        self.server = kwargs.get("server", None)
        self.secure = kwargs.get("secure", None)
        self.operator = kwargs.get("operator", None)
        self.signon = kwargs.get("signon", None)
        self.ip = kwargs.get("ip", None)
        self.realhost = kwargs.get("realhost", None)
        self.channels = IRCDefaultDict(case, set)

    def __repr__(self):
        keys = ("nick", "username", "host", "gecos", "account", "server",
                "secure", "operator", "signon", "ip", "realhost", "channels")

        # key={0.key!r}
        rep = ["{0}={{0.{0}!r}}".format(k) for k in keys]

        # Final format
        rep = "User({})".format(", ".join(rep))
        return rep.format(self)


class UserTrack(BaseExtension):

    """Track various user metrics, such as account info, and some channel
    tracking.

    This extension adds ``base.user_track`` as itself as an alias for
    ``get_extension("UserlTrack").``.

    :ivar users:
        Mapping of users, where the keys are casemapped nicks, and values are
        User instances. You should probably prefer
        :py:class:`~PyIRC.extensions.usertrack.Usertrack.get_user` to direct
        lookups on this dictionary.

    """

    caps = {
        "account-notify": [],
        "away-notify": [],
        "chghost": [],
    }

    requires = ["BasicRFC", "ISupport", "BaseTrack"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base.user_track = self

        self.u_expire_timers = IRCDict(self.case)
        self.who_timers = IRCDict(self.case)

        self.users = IRCDict(self.case)
        self.whois_send = IRCSet(self.case)

        # Authentication callbacks
        self.auth_cb = IRCDefaultDict(self.case, list)

        # WHOX sent list
        self.whox_send = list()

        # Whether or not to time users out
        self.do_timeout = kwargs.get("do_timeout", True)
        self.timeout = kwargs.get("timeout", 30)

        # Remove a user when they are out of all channels (used by MONITOR)
        self.remove_no_channels = True

        # Create ourselves
        basicrfc = self.base.basic_rfc
        self.add_user(basicrfc.nick, user=self.username,
                      gecos=self.gecos)

    def authenticate(self, nick, callback):
        """Get authentication for a user and return result in a callback.

        :param nick:
            Nickname of user to check authentication for

        :param callback:
            Callback to call for user when authentication is discovered. The
            User instance is passed in as the first parameter, or None if the
            user is not found. Use functools.partial to pass other arguments.

        """
        user = self.get_user(nick)
        if not user:
            # Add a user for now, get details later.
            self.users[nick] = User(self.case, nick)

        if user.account is not None:
            # User account is known
            callback(user)
        elif nick not in self.whois_send:
            # Defer for a whois
            self.auth_cb[nick].append(callback)
            self.send("WHOIS", ["*", user.nick])
            self.whois_send.add(nick)

    def get_user(self, nick):
        """Retrieve a user from the tracking dictionary based on nick.

        Use of this method is preferred to directly accessing the user
        dictionary.

        :param nick:
            Nickname of the user to retrieve.

        :returns: A :class:`User` instance, or None if user not found.

        """
        return self.users.get(nick)

    def add_user(self, nick, **kwargs):
        """Add a user to the tracking dictionary.

        Avoid using this method directly unless you know what you are
        doing.

        """
        user = self.get_user(nick)
        if not user:
            user = User(self.case, nick, **kwargs)
            self.users[nick] = user

        self.call_event("user", "user_create", user)

        return user

    def remove_user(self, nick):
        """Remove a user from the tracking dictionary.

        Avoid using this method directly unless you know what you are
        doing.

        """
        if nick not in self.users:
            _logger.warning("Deleting nonexistent user: %s", nick)
            return

        self.call_event("user", "user_delete", self.users[nick])

        _logger.debug("Deleted user: %s", nick)

        del self.users[nick]

    def timeout_user(self, nick):
        """Time a user out, cancelling existing timeouts.

        Avoid using this method directly unless you know what you are
        doing.

        """
        if not self.do_timeout:
            return

        if nick in self.u_expire_timers:
            self.unschedule(self.u_expire_timers[nick])

        callback = partial(self.remove_user, nick)
        self.u_expire_timers[nick] = self.schedule(self.timeout, callback)

    def update_username_host(self, hostmask_or_line):
        """Update a user's basic info, based on line hostmask info.

        Avoid using this method directly unless you know what you are doing.

        .. note::
            This mostly exists for brain-dead networks that don't quit users
            when they get cloaked.

        """
        if hasattr(hostmask_or_line, 'hostmask'):
            hostmask = hostmask_or_line.hostmask
        elif hasattr(hostmask_or_line, 'nick'):
            hostmask = hostmask_or_line
        else:
            raise ValueError("Expected a Hostmask or Line instance")

        if not hostmask or hostmask.nick:
            return

        user = self.get_user(hostmask.nick)
        if not user:
            return

        # Update
        user.nick = hostmask.nick

        if hostmask.username:
            user.username = hostmask.username

        if hostmask.host:
            user.host = hostmask.host

    @event("protocol", "case_change")
    def case_change(self, _):
        case = self.case

        self.u_expire_timers = self.u_expire_timers.convert(case)
        self.who_timers = self.who_timers.convert(case)

        self.users = self.users.convert(case)
        self.whois_send = self.whois_send.convert(case)

        self.auth_cb = self.auth_cb.convert(case)

    @event("link", "disconnected")
    def close(self, _):
        timers = chain(self.u_expire_timers.values(),
                       self.who_timers.values())
        for timer in timers:
            try:
                self.unschedule(timer)
            except ValueError:
                pass

        self.users.clear()
        self.whox_send.clear()

    @event("modes", "mode_prefix")
    def prefix(self, _, setter, target, mode):
        """Update the channel mode of a user."""
        # pylint: disable=unused-argument
        # Parse into hostmask in case of usernames-in-host
        hostmask = Hostmask.parse(mode.param)

        assert hostmask

        user = self.get_user(hostmask.nick)
        assert user

        channel = user.channels[target]
        if mode.adding:
            channel.add(mode.mode)
        else:
            channel.discard(mode.mode)

    @event("scope", "user_burst")
    def burst(self, _, scope):
        """Create or update users from a join burst."""
        target = scope.target
        channel = scope.scope
        modes = {m[0] for m in scope.modes} if scope.modes else set()

        # User no longer expiring
        self.u_expire_timers.pop(target.nick, None)

        user = self.get_user(target.nick)
        if not user:
            user = self.add_user(target.nick, username=target.username,
                                 host=target.host, gecos=scope.gecos,
                                 account=scope.account)
        else:
            self.update_username_host(target)

        # Add the channel
        user.channels[channel] = modes

    @event("scope", "user_join")
    def join(self, caller, scope):
        """Handle a user join.  Schedule a WHO(X) for them."""
        self.burst(caller, scope)

        target = scope.target
        channel = scope.scope

        basicrfc = self.base.basic_rfc
        if self.casecmp(target.nick, basicrfc.nick):
            # It's us!
            isupport = self.base.isupport
            params = [channel]
            if isupport.get("WHOX"):
                # Use WHOX if possible
                num = ''.join(str(randint(0, 9)) for x in range(randint(1, 3)))
                params.append("%tcuihsnflar," + num)
                self.whox_send.append(num)

            sched = self.schedule(2, partial(self.send, "WHO", params))
            self.who_timers[channel] = sched

    @event("scope", "user_part")
    @event("scope", "user_kick")
    def part(self, _, scope):
        """Handle a user leaving, possibly removing them if we no longer share
        any channels with them."""
        target = scope.target
        channel = scope.scope

        user = self.get_user(target.nick)
        if not user:
            _logger.warning("Got a part/kick for a user not found: %s (in %s)",
                            target.nick, channel)
            return
        elif channel not in user.channels:
            _logger.warning("Got a part/kick for a user not in a channel: %s "
                            "(in %s)", target.nick, channel)
            return

        user.channels.pop(channel)

        basicrfc = self.base.basic_rfc
        if self.casecmp(target.nick, basicrfc.nick):
            # We left the channel, scan all users to remove unneeded ones
            for u_nick, u_user in list(self.users.items()):
                if channel in u_user.channels:
                    # Purge from the cache since we don't know for certain.
                    del u_user.channels[channel]

                if self.casecmp(u_nick, basicrfc.nick):
                    # Don't delete ourselves!
                    continue

                if not u_user.channels:
                    # Delete the user outright to purge any cached data
                    # The data must be considered invalid when we leave
                    # TODO - possible MONITOR support?
                    self.remove_user(u_nick)
                    continue

        elif not user.channels:
            if self.do_timeout:
                self.timeout_user(target.nick)
            elif self.remove_no_channels:
                self.remove_user(target.nick)

    @event("scope", "user_quit")
    def quit(self, _, scope):
        """Remove a user from tracking since they have quit."""
        # User's gone
        self.remove_user(scope.target.nick)

    @event("commands", Numerics.RPL_WELCOME)
    def welcome(self, _, line):
        """Retrieve our current host on-connect."""
        # Obtain our own host
        self.send("USERHOST", [line.params[0]])

    @event("commands", Numerics.RPL_USERHOST)
    def userhost(self, _, line):
        """Update a user's host - possibly our own."""
        params = line.params
        if not (len(params) > 1 and params[1]):
            return

        basicrfc = self.base.basic_rfc

        for mask in params[1].split(' '):
            if not mask:
                continue

            parse = userhost_parse(mask)
            hostmask = parse.hostmask
            user = self.get_user(hostmask.nick)
            if not user:
                continue

            if hostmask.username:
                user.username = hostmask.username

            user.operator = parse.operator
            if not parse.away:
                user.away = False

            if self.casecmp(hostmask.nick, basicrfc.nick):
                user.realhost = hostmask.host
            else:
                user.host = hostmask.host

    @event("commands", Numerics.RPL_HOSTHIDDEN)
    def host_hidden(self, _, line):
        """Update our own host."""
        params = line.params

        user = self.get_user(params[0])
        assert user  # This should NEVER fire!

        user.host = params[1]

    @event("commands", "ACCOUNT")
    def account(self, _, line):
        """Update a user's account information."""
        self.update_username_host(line)

        account = line.params[0]

        user = self.get_user(line.hostmask.nick)
        assert user

        user.account = '' if account == '*' else account

        if user.nick in self.auth_cb:
            # User is awaiting authentication
            for callback in self.auth_cb[user.nick]:
                callback(user)

            del self.auth_cb[user.nick]

    @event("commands", "AWAY")
    def away(self, _, line):
        """Update a user's away flag."""
        self.update_username_host(line)

        user = self.get_user(line.hostmask.nick)
        assert user

        user.away = bool(line.params)

    @event("commands", "CHGHOST")
    def chghost(self, _, line):
        # NB - we don't know if a user is cloaking or uncloaking, or changing
        # cloak, so do NOT update user's cloak.
        self.update_username_host(line)

        user = self.get_user(line.hostmask.nick)
        assert user

        user.username = line.params[0]
        user.host = line.params[1]

    @event("commands", "NICK")
    def nick(self, _, line):
        """Update a user's nickname."""
        self.update_username_host(line)

        oldnick = line.hostmask.nick
        newnick = line.params[0]

        assert self.get_user(oldnick)

        self.users[newnick] = self.get_user(oldnick)
        self.users[newnick].nick = newnick

        del self.users[oldnick]

    @event("commands", Numerics.ERR_NOSUCHNICK)
    def notfound(self, _, line):
        """Remove a non-existent user."""
        nick = line.params[1]
        if nick in self.auth_cb:
            # User doesn't exist, call back
            for callback in self.auth_cb[nick]:
                callback(None)

            del self.auth_cb[nick]

        self.remove_user(nick)

    @event("commands", "PRIVMSG")
    @event("commands", "NOTICE")
    def message(self, _, line):
        if line.params[0] == '*':
            # We are not registered, do nothing.
            return

        hostmask = line.hostmask
        if not hostmask.nick:
            return

        if hostmask.nick in self.u_expire_timers:
            # User is expiring
            user = self.get_user(hostmask.nick)
            if hostmask.username != user.username or hostmask.host != user.host:
                # User is suspect, delete and find out more.
                self.remove_user(hostmask.nick)
            else:
                # Rearm timeout
                self.timeout_user(hostmask.nick)

        if not self.get_user(hostmask.nick):
            if not self.do_timeout:
                return

            # Obtain more information about the user
            user = self.add_user(hostmask.nick, user=hostmask.username,
                                 host=hostmask.host)

            if hostmask.nick not in self.whois_send:
                self.send("WHOIS", ['*', hostmask.nick])
                self.whois_send.add(hostmask.nick)

            self.timeout_user(hostmask.nick)

    @event("commands", Numerics.RPL_ENDOFWHO)
    def who_end(self, _, line):
        if not self.whox_send:
            return

        channel = line.params[1]
        del self.who_timers[channel]
        del self.whox_send[0]

    @event("commands", Numerics.RPL_ENDOFWHOIS)
    def whois_end(self, _, line):
        """Finish updating a user's information."""
        nick = line.params[1]

        self.whois_send.discard(nick)

        user = self.get_user(nick)

        # If the user is awaiting auth, we aren't gonna find out their auth
        # status through whois. If it's not in whois, we probably aren't going
        # to find it any other way (sensibly at least).
        if nick in self.auth_cb:
            # User is awaiting authentication
            for callback in self.auth_cb[nick]:
                callback(user)

            del self.auth_cb[nick]

    @event("commands", Numerics.RPL_WHOISUSER)
    def whois_user(self, _, line):
        """Update a user's identity information."""
        nick = line.params[1]
        username = line.params[2]
        host = line.params[3]
        gecos = line.params[5]

        user = self.get_user(nick)
        if not user:
            return

        user.nick = nick
        user.username = username
        user.host = host
        user.gecos = gecos

    @event("commands", Numerics.RPL_WHOISCHANNELS)
    def whois_channels(self, _, line):
        """Update a user's channel set."""
        user = self.get_user(line.params[1])
        if not user:
            return

        isupport = self.base.isupport
        prefix = prefix_parse(isupport.get("PREFIX"))

        for channel in line.params[-1].split():
            mode = set()
            mode, channel = status_prefix_parse(channel, prefix)
            user.channels[channel] = mode

    @event("commands", Numerics.RPL_WHOISHOST)
    def whois_host(self, _, line):
        """Update a user's IP and/or host."""
        user = self.get_user(line.params[1])
        if not user:
            return

        # Fucking unreal did this shit.
        string, _, ip = line.params[-1].rpartition(' ')
        string, _, realhost = string.rpartition(' ')

        user.ip = ip
        user.realhost = realhost

    @event("commands", Numerics.RPL_WHOISIDLE)
    def whois_idle(self, _, line):
        user = self.get_user(line.params[1])
        if not user:
            return

        user.signon = int(line.params[3])

    @event("commands", Numerics.RPL_WHOISOPERATOR)
    def whois_operator(self, _, line):
        """Update a user's operator flag."""
        user = self.get_user(line.params[1])
        if not user:
            return

        user.operator = True

    @event("commands", Numerics.RPL_WHOISSECURE)
    def whois_secure(self, _, line):
        """Update a user's SSL flag."""
        user = self.get_user(line.params[1])
        if not user:
            return

        user.secure = True

    @event("commands", Numerics.RPL_WHOISSERVER)
    def whois_server(self, _, line):
        """Update a user's currently connected server name."""
        user = self.get_user(line.params[1])
        if not user:
            return

        user.server = line.params[2]
        user.server_desc = line.params[3]

    @event("commands", Numerics.RPL_WHOISLOGGEDIN)
    def whois_account(self, _, line):
        """Update a user's account, possibly firing auth callbacks."""
        user = self.get_user(line.params[1])
        if not user:
            return

        user.account = line.params[2]

        nick = user.nick
        if nick in self.auth_cb:
            # User is awaiting authentication
            for callback in self.auth_cb[nick]:
                callback(user)

            del self.auth_cb[nick]

    @event("commands", Numerics.RPL_WHOREPLY)
    def who(self, _, line):
        """Process a WHO response, updating the corresponding user object."""
        if len(line.params) < 8:
            # Some bizarre RFC breaking server
            _logger.warn("Malformed WHO from server")
            return

        channel = line.params[1]
        username = line.params[2]
        host = line.params[3]
        server = line.params[4]
        nick = line.params[5]
        flags = who_flag_parse(line.params[6])
        other = line.params[7]
        hopcount, _, other = other.partition(' ')

        user = self.get_user(nick)
        if not user:
            return

        isupport = self.base.isupport

        if isupport.get("RFC2812"):
            # IRCNet, for some stupid braindead reason, sends SID here. Why? I
            # don't know. They mentioned it might break clients in the commit
            # log. I really have no idea why it exists, why it's useful to
            # anyone, or anything like that. But honestly, WHO sucks enough...
            sid, _, gecos = other.partition(' ')
        else:
            sid = None
            gecos = other

        if channel != '*':
            # Convert symbols to modes
            prefix = prefix_parse(isupport.get("PREFIX")).prefix_to_mode

            mode = set()
            for char in flags.modes:
                char = prefix.get(char)
                if char is not None:
                    mode.add(char)

            user.channels[channel] = mode

        away = flags.away
        operator = flags.operator

        # NB - these two members aren't guaranteed to exist (yet?)
        user.sid = sid
        user.server = server

        user.username = username
        user.host = host
        user.gecos = gecos
        user.away = away
        user.operator = operator

    @event("commands", Numerics.RPL_WHOSPCRPL)
    def whox(self, _, line):
        """Process a WHOX response, updating the corresponding user object."""
        if len(line.params) != 12:
            # Not from us!
            return

        # Verify the server supports WHOX for real because Bahamut has its own
        # Eldritch abomination we don't support (RWHO... you don't wanna know)
        isupport = self.base.isupport
        if not isupport.get("WHOX"):
            return

        whoxid = line.params[1]
        channel = line.params[2]
        username = line.params[3]
        ip = line.params[4]
        host = line.params[5]
        server = line.params[6]
        nick = line.params[7]
        flags = who_flag_parse(line.params[8])
        idle = line.params[9]
        account = line.params[10]
        gecos = line.params[11]

        user = self.get_user(nick)
        if not user:
            return

        if whoxid not in self.whox_send:
            # Not sent by us, weird!
            return

        if channel != '*':
            # Convert symbols to modes
            prefix = prefix_parse(isupport.get("PREFIX")).prefix_to_mode

            mode = set()
            for char in flags.modes:
                char = prefix.get(char)
                if char is not None:
                    mode.add(char)

            user.channels[channel] = mode

        away = flags.away
        operator = flags.operator

        if account == '0':
            # Not logged in
            account = ''

        if ip == '255.255.255.255':
            # Cloaked
            ip = None

        user.server = server
        user.idle = idle
        user.username = username
        user.host = host
        user.server = server
        user.gecos = gecos
        user.away = away
        user.operator = operator
        user.account = account
        user.ip = ip


class MonitorUserTrack(BaseExtension):

    """Support for the MONITOR extension.

    This works in tandem with :py:class:`~PyIRC.extensions.usertrack.UserTrack`
    to remove users as-needed.
    """

    requires = ["UserTrack", "ISupport"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get max number of monitorable users
        max_monitor = self.base.isupport.get("MONITOR")
        if max_monitor is None:
            _logger.warn("Could not use MonitorUserTrack extension on server "
                         "because it is not supported.")
            self._usable = False
            return

        self.max_monitor = max_monitor

        self._usable = True

        # Users we (the extension) are monitoring
        self.monitoring = IRCSet()

        # Users being monitored outside the extension
        self.ext_monitoring = IRCSet()

        # Unset
        user_track = self.base.user_track
        user_track.remove_no_channels = False

    def monitor(self, *args):
        """Monitor the given nicknames.

        This is the preferred API for setting MONITORs.
        """
        if not args:
            raise ValueError("Must have at least one nickname to monitor")

        nicks = []
        monitors = self.monitoring + self.ext_monitoring
        for nick in args:
            if nick not in monitors:
                nicks.append(nick)

            self.ext_monitoring.add(nick)

        if nicks:
            self.send("MONITOR", ["+", ",".join(nicks)])

    def unmonitor(self, *args):
        """Unmonitor the given nicknames.

        This is the preferred API for unsetting MONITORs.
        """
        if not args:
            raise ValueError("Must have at least one nickname to unmonitor")

        for nick in args:
            if nick in self.monitoring:
                # Don't remove nicks we are monitoring for in the extension.
                continue
            elif nick in self.ext_monitoring:
                self.ext_monitoring.delete(nick)
                nicks.append(nick)

        if nicks:
            self.send("MONITOR", ["-", ",".join(nicks)])

    @event("commands_out", "MONITOR")
    def monitor_out(self, _, line):
        if len(line.params) < 2:
            return

        user_track = self.base.user_track
        users = line.params[1].split(",")
        if line.params[0] == "+":
            for nick in users:
                if nick in self.monitoring:
                    continue

                self.ext_monitoring.add(nick)
        elif line.params[0] == "-":
            for nick in users:
                if nick in self.monitoring:
                    # The user doesn't want them tracked, fine.
                    user_track.user_remove(nick)
                    self.monitoring.delete(nick)

                self.ext_monitoring.discard(nick)

    @event("commands", Numerics.RPL_MONONLINE)
    def monitor_online(self, _, line):
        """Add users who come online on MONITOR."""
        if not self._usable:
            return

        monitor = [Hostmask.parse(h) for h in line.params[-1].split(",")]
        if not monitor:
            return

        user_track = self.base.user_track
        for user in monitor:
            user_track.add_user(user.nick, username=user.username,
                                host=user.host)

    @event("commands", Numerics.RPL_MONOFFLINE)
    def monitor_offline(self, _, line):
        """Remove users who go offline on MONITOR."""
        if not self._usable:
            return

        monitor = [Hostmask.parse(h) for h in line.params[-1].split(",")]
        if not monitor:
            return

        user_track = self.base.user_track
        for user in monitor:
            if user_track.get_user(user.nick):
                user_track.remove_user(user.nick)

    @event("scope", "user_part", priority=10000)  # Ensure this comes last
    @event("scope", "user_kick", priority=10000)
    def part(self, _, scope):
        """Handle a user parting, registering them for monitoring."""
        if not self._usable:
            return

        target = scope.target
        nick = target.nick
        user_track = self.base.user_track

        user = user_track.get_user(nick)
        if not user or user.channels:
            return

        if len(self.monitoring + self.ext_monitoring) >= self.max_monitor:
            # Delete the user, we're out of space!
            user_track.remove_user(nick)
            return

        if nick in self.monitoring:
            return

        self.monitoring.add(nick)
        self.send("MONITOR", ["+", nick])

    @event("user", "user_delete")
    def user_delete(self, user):
        """Handle when a user is deleted."""
        if user.nick in self.monitoring:
            self.monitoring.delete(user.nick)
            if user not in self.ext_monitoring:
                self.send("MONITOR", ["-", user.nick])
