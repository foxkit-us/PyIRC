# Copyright © 2013-2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.

from random import randint
from functools import partial
from logging import getLogger

from PyIRC.base import BaseExtension
from PyIRC.casemapping import IRCString
from PyIRC.line import Hostmask
from PyIRC.numerics import Numerics
from PyIRC.mode import mode_parse, prefix_parse, who_flag_parse


logger = getLogger(__name__)


class User:

    """ A user entity. """

    def __init__(self, nick, **kwargs):
        assert nick is not None

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

        # Statuses in channels
        self.chan_status = dict()

        logger.debug("Created user: %s", self.nick)

    def __repr__(self):
        nick = self.nick
        username = self.username
        host = self.host
        gecos = self.gecos
        account = self.account
        server = self.server
        secure = self.secure
        operator = self.operator
        signon = self.signon
        ip = self.ip
        realhost = self.realhost

        # Build format string
        fmt = []
        for k, v in locals().items():
            if v is None or k in ('k', 'v', 'fmt'):
                continue

            fmt.append('{}={}'.format(k, v))

        return "User({})".format(', '.join(fmt))


class UserTrack(BaseExtension):

    """ Track various user metrics, such as account info """

    caps = {
        "account-notify" : [],
        "away-notify" : [],
        "chghost" : [],
        "extended-join" : [],
        "multi-prefix" : [],
        "userhost-in-names" : [],
    }

    def __init__(self, base, **kwargs):

        self.base = base

        self.commands = {
            "ACCOUNT" : self.account,
            "AWAY" : self.away,
            "CHGHOST" : self.chghost,
            "JOIN" : self.join,
            "KICK" : self.part,
            "MODE" : self.mode,
            "NICK" : self.nick,
            "NOTICE" : self.message,
            "PART" : self.part,
            "PRIVMSG" : self.message,
            "QUIT" : self.quit,
            Numerics.ERR_NOSUCHNICK : self.notfound,
            Numerics.RPL_NAMREPLY : self.names,
            Numerics.RPL_ENDOFWHO : self.who_end,
            Numerics.RPL_WHOISUSER : self.whois_user,
            Numerics.RPL_WHOISCHANNELS : self.whois_channels,
            Numerics.RPL_WHOISHOST : self.whois_host,
            Numerics.RPL_WHOISIDLE : self.whois_idle,
            Numerics.RPL_WHOISOPERATOR : self.whois_operator,
            Numerics.RPL_WHOISSECURE : self.whois_secure,
            Numerics.RPL_WHOISSERVER : self.whois_server,
            Numerics.RPL_WHOISLOGGEDIN : self.whois_login,
            Numerics.RPL_WHOREPLY : self.who,
            Numerics.RPL_WHOSPCRPL : self.whox,
        }

        self.requires = ["ISupport"]

        self.u_expire_timers = dict()
        self.who_timers = dict()

        self.users = dict()
        self.whox_send = list()

        # Create ourselves
        self.add_user(self.base.nick, user=self.base.username,
                      gecos=self.base.gecos)

    def casefold(self, nick):
        # TODO - move this into a lower class like base

        isupport = self.get_extension("ISupport")
        casefold = isupport.supported.get("CASEMAPPING", "RFC1459")

        if casefold == "ASCII":
            return IRCString.ascii_casefold(nick)
        elif casefold == "RFC1459":
            return IRCString.rfc1459_casefold(nick)
        else:
            return nick.casefold()

    def get_user(self, nick):
        """ Get a user, or None if nonexistent """

        return self.users.get(self.casefold(nick))

    def add_user(self, nick, **kwargs):
        """ Add a user """

        user = self.get_user(nick)
        if not user:
            user = User(nick, **kwargs)
            self.users[self.casefold(nick)] = user

        return user

    def remove_user(self, nick):
        """ Callback to remove a user """

        nick = self.casefold(nick)
        if nick not in self.users:
            logger.warning("Deleting nonexistent user: %s", user)
            return

        logger.debug("Deleted user: %s", nick)

        del self.users[nick]

    def timeout_user(self, nick):
        """ Time a user out, cancelling existing timeouts """

        nick = self.casefold(nick)
        if nick in self.u_expire_timers:
            self.unschedule(self.u_expire_timers[nick])

        callback = partial(self.remove_user, nick)
        self.u_expire_timers[nick] = self.schedule(30, callback)

    def update_username_host(self, line):
        """ Update a user's basic info """

        if not line.hostmask or not line.hostmask.nick:
            return

        hostmask = line.hostmask
        user = self.get_user(hostmask.nick)
        if not user:
            return

        if hostmask.username:
            user.username = hostmask.username

        if hostmask.host:
            user.host = hostmask.host

    def account(self, event):
        """ Get account changes """

        self.update_username_host(event.line)

        user = self.get_user(event.line.hostmask.nick)
        assert user

        user.account = '' if account == '*' else account

    def away(self, event):
        """ Get away status changes """

        self.update_username_host(event.line)

        user = self.get_user(event.line.hostmask.nick)
        assert user

        user.away = bool(event.line.params)

    def chghost(self, event):
        """ Update a user's host """

        self.update_username_host(event.line)

        user = self.get_user(event.line.hostmask.nick)
        assert user

        user.username = event.line.params[0]
        user.host = event.line.params[1]

    def join(self, event):
        """ Introduce a user """

        channel = event.line.params[0]
        nick = event.line.hostmask.nick

        user = self.get_user(nick)
        if user:
            # Remove any pending expiration timer
            self.u_expire_timers.pop(self.casefold(nick), None)
        else:
            # Create a new user with available info
            cap_negotiate = self.get_extension("CapNegotiate")
            if cap_negotiate and 'extended-join' in cap_negotiate.local:
                account = event.line.params[1]
                if account == '*':
                    account = ''

                gecos = event.line.params[2]

            user = self.add_user(nick, account=account, gecos=gecos)

        # Update info
        self.update_username_host(event.line)

        if self.casefold(nick) == self.casefold(self.base.nick):
            # It's us!
            isupport = self.get_extension("ISupport")

            params = [channel]
            if "WHOX" in isupport.supported:
                # Use WHOX if possible
                num = ''.join(str(randint(0, 9)) for x in range(randint(1, 3)))
                params.append("%tcuihsnflar,"+num)
                self.whox_send.append(num)

            sched = self.schedule(2, partial(self.send, "WHO", params))
            self.who_timers[self.casefold(channel)] = sched

        # Add the channel
        user.chan_status[self.casefold(channel)] = set()

    def mode(self, event):
        """ Got a channel mode """

        self.update_username_host(event.line)

        isupport = self.get_extension("ISupport")
        chantypes = isupport.supported.get("CHANTYPES", '#+!&')

        prefix = isupport.supported.get("PREFIX", None)
        if prefix is None:
            prefix = "(ov)@+"

        prefix = prefix_parse(prefix)

        channel = self.casefold(event.line.params[0])

        # Don't care if user-directed, as that means us most of the time
        if not channel.startswith(*chantypes):
            return

        mode_add, mode_del = mode_parse(event.line.params[1],
                                        event.line.params[2:])

        for nick, mode in mode_add.items():
            if not mode.intersection(prefix.keys()):
                # Status modes are what we care about
                continue

            user = self.get_user(nick)
            if not user:
                logger.warn("Buggy IRC server sent us mode %s for " \
                    "nonexistent user: %s", mode, user)
                continue

            chan_status = user.chan_status[channel]
            chan_status.update(mode)

        for user, mode in mode_del.items():
            if mode not in prefix:
                continue

            user = self.get_user(nick)
            if not user:
                logger.warn("Buggy IRC server sent us mode %s for " \
                    "nonexistent user: %s", mode, user)
                continue

            chan_status = user.chan_status[channel]
            chan_status.difference_update(mode)

        cap_negotiate = self.get_extension("CapNegotiate")
        if mode_del and not (cap_negotiate and 'multi-prefix' in
                             cap_negotiate.local):
            # Reissue a names request if we don't have multi-prefix
            self.send("NAMES", [channel])

    def nick(self, event):
        """ User changed nick """

        self.update_username_host(event.line)

        oldnick = event.line.hostmask.nick
        newnick = event.line.params[0]

        assert self.get_user(oldnick)

        self.users[self.casefold(newnick)] = self.get_user(oldnick)
        self.users[self.casefold(newnick)].nick = newnick

        del self.users[self.casefold(oldnick)]

    def notfound(self, event):
        """ User is gone """

        self.remove_user(event.line.params[1])

    def message(self, event):
        """ Got a message from a user """

        hostmask = event.line.hostmask

        if event.line.params[0] == '*':
            # Us before reg.
            return

        if self.casefold(hostmask.nick) in self.u_expire_timers:
            # User is expiring
            user = self.get_user(hostmask.nick)
            if hostmask.username != user.username or hostmask.host != user.host:
                # User is suspect, delete and find out more.
                self.remove_user(hostmask.nick)
            else:
                # Rearm timeout
                self.timeout_user(hostmask.nick)

        if not self.get_user(hostmask.nick):
            # Obtain more information about the user
            user = self.add_user(hostmask.nick, user=hostmask.username,
                                 host=hostmask.host)

            self.send("WHOIS", ['*', hostmask.nick])

            self.timeout_user(hostmask.nick)

    def part(self, event):
        """ Exit a user """

        channel = self.casefold(event.line.params[0])

        user = self.get_user(event.line.hostmask.nick)
        assert user

        assert channel in user.chan_status
        del user.chan_status[channel]

        if event.line.hostmask.nick == self.base.nick:
            # We left the channel, scan all users to remove unneeded ones
            for u_nick, u_user in list(self.users.items()):
                if len(u_user.chan_status) > 1:
                    # Not interested
                    continue
                elif self.casefold(u_nick) == self.casefold(self.base.nick):
                    # Don't expire ourselves!
                    continue
                elif channel in u_user.chan_status:
                    # Delete the user outright to purge any cached data
                    # The data must be considered invalid when we leave
                    # TODO - possible MONITOR support?
                    self.remove_user(u_nick)

        elif not user.chan_status:
            # No more channels and not us, delete
            # TODO - possible MONITOR support?
            self.remove_user(event.line.hostmask.nick)

    def quit(self, event):
        """ Exit a user for real """

        assert self.casefold(event.line.hostmask.nick) in self.users
        self.remove_user(event.line.hostmask.nick)

    def names(self, event):
        """ Process a channel NAMES event """

        channel = self.casefold(event.line.params[2])

        isupport = self.get_extension("ISupport")
        prefix = isupport.supported.get("PREFIX", None)
        if prefix is None:
            prefix = "(ov)@+"

        prefix = prefix_parse(prefix)
        pmap = {v : k for k, v in prefix.items()}

        for user in event.line.params[-1].split():
            mode = set()
            while user[0] in pmap:
                # Accomodate multi-prefix
                prefix, user = user[0], user[1:]
                mode.add(pmap[prefix])

            # userhost-in-names (no need to check, nick goes through this
            # just fine)
            hostmask = Hostmask.parse(user)
            username = hostmask.username if hostmask.username else None
            host = hostmask.host if hostmask.host else None

            user = self.get_user(hostmask.nick)
            if user:
                # Update user info
                if username:
                    user.username = username

                if host:
                    user.host = host
            else:
                user = self.add_user(hostmask.nick, user=username, host=host)

            # Apply modes
            user.chan_status[channel] = mode

    def who_end(self, event):
        """ Process end of WHO reply """

        if not self.whox_send:
            return

        del self.whox_send[0]

    def whois_user(self, event):
        """ The nickname/user/host/gecos of a user """

        nick = event.line.params[1]
        username = event.line.params[2]
        host = event.line.params[3]
        gecos = event.line.params[5]

        user = self.get_user(nick)
        if not user:
            return

        user.username = username
        user.host = host
        user.gecos = gecos

    def whois_channels(self, event):
        """ Channels user is on from WHOIS """

        user = self.get_user(event.line.params[1])
        if not user:
            return

        isupport = self.get_extension("ISupport")
        prefix = isupport.supported.get("PREFIX", None)
        if prefix is None:
            prefix = "(ov)@+"

        prefix = prefix_parse(prefix)
        pmap = {v : k for k, v in prefix.items()}

        for channel in event.line.params[-1].split():
            mode = set()
            while user[0] in pmap:
                # Accomodate multi-prefix
                prefix, user = user[0], user[1:]
                mode.add(pmap[prefix])

            user.chan_status[self.casefold(channel)] = mode

    def whois_host(self, event):
        """ Real host of the user (usually oper only) in WHOIS """

        user = self.get_user(event.line.params[1])
        if not user:
            return

        # Fucking unreal.
        string, _, ip = event.line.params[-1].rpartition(' ')
        string, _, realhost = string.rpartition(' ')

        user.ip = ip
        user.realhost = realhost

    def whois_idle(self, event):
        """ Idle and signon time for user from WHOIS  """

        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.signon = event.line.params[3]

    def whois_operator(self, event):
        """ User is an operator according to WHOIS """

        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.operator = True

    def whois_secure(self, event):
        """ User is known to be using SSL from WHOIS """

        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.secure = True

    def whois_server(self, event):
        """ Server the user is logged in on from WHOIS """

        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.server = event.line.params[2]
        user.server_desc = event.line.params[3]

    def whois_login(self, event):
        """ Services account name of user according to WHOIS """

        # FIXME - users account names aren't unset if not found in whois.

        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.account = event.line.params[2]

    def who(self, event):
        """ Process a response to WHO """

        if len(event.line.params) < 8:
            # Some bizarre RFC breaking server
            logger.warn("Malformed WHO from server")
            return

        channel = self.casefold(event.line.params[1])
        username = event.line.params[2]
        host = event.line.params[3]
        server = event.line.params[4]
        nick = event.line.params[5]
        flags = who_flag_parse(event.line.params[6])
        other = event.line.params[7]
        hopcount, _, other = other.partition(' ')

        user = self.get_user(nick)
        if not user:
            return

        isupport = self.get_extension("ISupport")

        if isupport.supported.get("RFC2812", False):
            # IRCNet, for some stupid braindead reason, sends SID here. Why? I
            # don't know. They mentioned it might break clients in the commit
            # log. I really have no idea why it exists, why it's useful to
            # anyone, or anything like that. But honestly, WHO sucks enough...
            sid, _, realname = other.partition(' ')
        else:
            sid = None
            realname = other

        if channel != '*':
            # Convert symbols to modes
            prefix = isupport.supported.get("PREFIX", None)
            if prefix is None:
                prefix = "(ov)@+"

            prefix = prefix_parse(prefix)
            pmap = {v : k for k, v in prefix.items()}

            mode = set()
            for m in flags.modes:
                m = pmap.get(m)
                if m is not None:
                    mode.add(m)

            user.chan_status[channel] = mode

        away = flags.away
        operator = flags.operator

        if account == '0':
            # Not logged in
            account = ''

        if ip == '255.255.255.255':
            # Cloaked
            ip = None

        user.username = username
        user.host = host
        user.gecos = gecos
        user.away = away
        user.operator = operator
        user.account = account
        user.ip = ip

    def whox(self, event):
        """ Parse WHOX responses """

        if len(event.line.params) != 12:
            # Not from us!
            return

        whoxid = event.line.params[1]
        channel = self.casefold(event.line.params[2])
        username = event.line.params[3]
        ip = event.line.params[4]
        host = event.line.params[5]
        server = event.line.params[6]
        nick = event.line.params[7]
        flags = who_flag_parse(event.line.params[8])
        #idle = event.line.params[9]
        account = event.line.params[10]
        gecos = event.line.params[11]

        user = self.get_user(nick)
        if not user:
            return

        if whoxid not in self.whox_send:
            # Not sent by us, weird!
            return

        if channel != '*':
            # Convert symbols to modes
            isupport = self.get_extension("ISupport")

            prefix = isupport.supported.get("PREFIX", None)
            if prefix is None:
                prefix = "(ov)@+"

            prefix = prefix_parse(prefix)
            pmap = {v : k for k, v in prefix.items()}

            mode = set()
            for m in flags.modes:
                m = pmap.get(m)
                if m is not None:
                    mode.add(m)

            user.chan_status[channel] = mode

        away = flags.away
        operator = flags.operator

        if account == '0':
            # Not logged in
            account = ''

        if ip == '255.255.255.255':
            # Cloaked
            ip = None

        user.username = username
        user.host = host
        user.server = server
        user.gecos = gecos
        user.away = away
        user.operator = operator
        user.account = account
        user.ip = ip
