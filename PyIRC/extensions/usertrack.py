# Copyright © 2013-2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.

from random import randint
from functools import partial
from logging import getLogger

from PyIRC.base import BaseExtension
from PyIRC.line import Hostmask
from PyIRC.numerics import Numerics
from PyIRC.mode import mode_parse, prefix_parse, who_flag_parse


logger = getLogger(__name__)


class User:

    """ A user entity. """

    def __init__(self, nick, **kwargs):
        self.nick = nick
        self.user = kwargs.get("user", None)
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

    def __repr__(self):
        nick = self.nick
        user = self.user
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

        self.user_expire_timers = dict()
        self.who_timers = dict()

        self.users = dict()
        self.whoxsend = list()

    def remove_user(self, user):
        """ Callback to remove a user """

        if user not in self.users:
            logger.warning("Deleting nonexistent user: %s", user)
            return

        del self.users[user]

    def update_user_host(self, line):
        """ Update a user's basic info """
        
        if not line.hostmask or not line.hostmask.nick:
            return

        hostmask = line.hostmask
        user = self.users[hostmask.nick]

        if hostmask.user:
            user.user = hostmask.user

        if hostmask.host:
            user.host = hostmask.host

    def account(self, event):
        """ Get account changes """

        assert event.line.hostmask.nick in self.users

        self.update_user_host(event.line)

        user = self.users[event.line.hostmask.nick]
        user.account = '' if account == '*' else account

    def away(self, event):
        """ Get away status changes """

        assert event.line.hostmask.nick in self.users

        self.update_user_host(event.line)

        user = self.users[event.line.hostmask.nick]
        user.away = bool(event.line.params)

    def chghost(self, event):
        """ Update a user's host """

        assert event.line.hostmask.nick in self.users

        self.update_user_host(event.line)

        user = self.users[event.line.hostmask.nick]
        user.user = event.line.params[0]
        user.host = event.line.params[1]

    def join(self, event):
        """ Introduce a user """

        channel = event.line.params[0]

        if event.line.hostmask.nick in self.users:
            user = self.users[event.line.hostmask.nick]

            # Also remove any pending expiration timer
            self.user_expire_timers.pop(event.line.hostmask.nick, None)
        else:
            # Create a new user with available info
            cap_negotiate = self.get_extension("CapNegotiate")
            if cap_negotiate and 'extended-join' in cap_negotiate.local:
                account = event.line.params[1]
                if account == '*':
                    account = ''

            gecos = event.line.params[2]

            user = User(event.line.hostmask.nick, account=account,
                        gecos=gecos)
            self.users[event.line.hostmask.nick] = user

        self.update_user_host(event.line)

        if event.line.hostmask.nick == self.base.nick:
            # It's us!
            isupport = self.get_extension("ISupport")

            params = [channel]
            if "WHOX" in isupport.supported:
                # Use WHOX if possible
                num = ''.join(str(randint(0, 9)) for x in range(randint(1, 3)))
                params.append("%tcuihsnflar,"+num)
                self.whoxsend.append(num)

            sched = self.schedule(2, partial(self.send, "WHO", params))
            self.who_timers[channel] = sched

    def mode(self, event):
        """ Got a channel mode """

        self.update_user_host(event.line)

        isupport = self.get_extension("ISupport")
        chantypes = isupport.supported.get("CHANTYPES", '#+!&')

        prefix = isupport.supported.get("PREFIX", None)
        if prefix is None:
            prefix = "(ov)@+"

        prefix = prefix_parse(prefix)

        channel = event.line.params[0]

        # Don't care if user-directed, as that means us most of the time
        if not channel.startswith(*chantypes):
            return

        mode_add, mode_del = mode_parse(event.line.params[1],
                                        event.line.params[2:])

        for user, mode in mode_add.items():
            if mode not in prefix:
                # Status modes are what we care about
                continue

            if user not in self.users:
                # Some buggy IRC server might send this
                logger.warn("Buggy IRC server sent us mode %s for " \
                    "nonexistent user: %s", mode, user)
                continue

            self.users[user].chan_status[channel].update(mode)

        for user, mode in mode_del.items():
            if mode not in prefix:
                continue

            if user not in self.users:
                logger.warn("Buggy IRC server sent us mode %s for " \
                    "nonexistent user: %s", mode, user)
                continue

            self.users[user].chan_status[channel].difference_update(mode)

        cap_negotiate = self.get_extension("CapNegotiate")
        if mode_del and not (cap_negotiate and 'multi-prefix' in
                             cap_negotiate.local):
            # Reissue a names request if we don't have multi-prefix
            self.send("NAMES", [channel])

    def nick(self, event):
        """ User changed nick """

        self.update_user_host(event.line)

        oldnick = event.line.hostmask.nick
        newnick = event.line.params[0]

        self.users[newnick] = self.users[oldnick]
        self.users[newnick].nick = newnick

        del self.users[oldnick]

    def message(self, event):
        """ Got a message from a user """

        hostmask = event.line.hostmask

        if event.line.params[0] == '*':
            # Us before reg.
            return

        expire = True
        if event.line.hostmask.nick in self.user_expire_timers:
            self.update_user_host(event.line)

            # Rearm any expiry timers
            self.unschedule(self.user_expire_timers[hostmask.nick])
        elif hostmask.nick not in self.users:
            # Obtain more information about the user
            user = User(hostmask.nick, user=hostmask.user, host=hostmask.host)
            self.users[hostmask.nick] = user

            self.send("WHOIS", [hostmask.nick] * 2)
        else:
            expire = False

        if expire:
            self.user_expire_timers[hostmask.nick] = self.schedule(30,
                partial(self.remove_user, hostmask.nick))

    def part(self, event):
        """ Exit a user """

        channel = event.line.params[0]

        assert event.line.hostmask.nick in self.users
        user = self.users[event.line.hostmask.nick]

        assert channel in user.chan_status
        del user.chan_status[channel]

        if event.line.hostmask.nick == self.base.nick:
            # Left the channel, scan all users
            for u_nick, u_user in self.users.items():
                if len(u_user.chan_status) > 1:
                    # Not interested
                    continue
                elif u_nick == self.base.nick:
                    # Don't expire ourselves!
                    continue
                elif channel in u_user.chan_status:
                    # Expire in 30 seconds if they are the only channel we
                    # know about that has them
                    sched = self.schedule(30, partial(self.remove_user,
                                                      u_nick))
                    self.user_expire_timers[u_nick] = sched

        elif not user.chan_status:
            # No more channels and not us, delete in 30 seconds
            sched = self.schedule(30, partial(self.remove_user,
                                              event.line.hostmask.nick))
            self.user_expire_timers[event.line.hostmask.nick] = sched

    def quit(self, event):
        """ Exit a user for real """

        assert event.line.hostmask.nick in self.users

        del self.users[event.line.hostmask.nick]

    def names(self, event):
        """ Process a channel NAMES event """

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
            user = hostmask.user if hostmask.user else None
            host = hostmask.host if hostmask.host else None

            if hostmask.nick in self.users:
                # Update user info
                if user:
                    self.users[hostmask.nick].user = user

                if host:
                    self.users[hostmask.nick].host = host
            else:
                self.users[hostmask.nick] = User(hostmask.nick, user=user,
                                                 host=host)

            # Apply modes
            self.users[hostmask.nick].chan_status = mode

    def who_end(self, event):
        """ Process end of WHO reply """

        if not self.whoxsend:
            return

        del self.whoxsend[0]

    def whois_user(self, event):
        """ The nickname/user/host/gecos of a user """

        nick = event.line.params[1]
        if nick not in self.users:
            return

        user = event.line.params[2]
        host = event.line.params[3]
        gecos = event.line.params[5]

        self.users[nick].user = user
        self.users[nick].host = host
        self.users[nick].gecos = gecos

    def whois_channels(self, event):
        """ Channels user is on from WHOIS """

        nick = event.line.params[1]
        if nick not in self.users:
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

            self.users[nick].chan_status[channel] = mode

    def whois_host(self, event):
        """ Real host of the user (usually oper only) in WHOIS """

        nick = event.line.params[1]
        if nick not in self.users:
            return

        # Fucking unreal.
        string, _, ip = event.line.params[-1].rpartition(' ')
        string, _, realhost = string.rpartition(' ')

        self.users[nick].ip = ip
        self.users[nick].realhost = realhost

    def whois_idle(self, event):
        """ Idle and signon time for user from WHOIS  """

        nick = event.line.params[1]
        if nick not in self.users:
            return

        self.users[nick].signon = event.line.params[3]

    def whois_operator(self, event):
        """ User is an operator according to WHOIS """
        
        nick = event.line.params[1]
        if nick not in self.users:
            return

        self.users[nick].operator = True

    def whois_secure(self, event):
        """ User is known to be using SSL from WHOIS """

        nick = event.line.params[1]
        if nick not in self.users:
            return

        self.users[nick].secure = True

    def whois_server(self, event):
        """ Server the user is logged in on from WHOIS """

        nick = event.line.params[1]
        if nick not in self.users:
            return

        self.users[nick].server = event.line.params[2]
        self.users[nick].server_desc = event.line.params[3]

    def whois_login(self, event):
        """ Services account name of user according to WHOIS """

        # FIXME - users account names aren't unset if not found in whois.

        nick = event.line.params[1]
        if nick not in self.users:
            return

        self.users[nick].account = event.line.params[2]

    def who(self, event):
        """ Process a response to WHO """

        if len(event.line.params) < 8:
            # Some bizarre RFC breaking server
            logger.warn("Malformed WHO from server")
            return

        channel = event.line.params[1]
        user = event.line.params[2]
        host = event.line.params[3]
        server = event.line.params[4]
        nick = event.line.params[5]
        flags = who_flag_parse(event.line.params[6])
        other = event.line.params[7]
        hopcount, _, other = other.partition(' ')

        if nick == '*' or nick not in self.users:
            # *shrug*
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

            self.users[nick].chan_status[channel] = mode

        away = flags.away
        operator = flags.operator

        if account == '0':
            # Not logged in
            account = ''

        if ip == '255.255.255.255':
            # Cloaked
            ip = None

        self.users[nick].user = user
        self.users[nick].host = host
        self.users[nick].gecos = gecos
        self.users[nick].away = away
        self.users[nick].operator = operator
        self.users[nick].account = account
        self.users[nick].ip = ip

    def whox(self, event):
        """ Parse WHOX responses """

        if len(event.line.params) != 12:
            # Not from us!
            return

        whoxid = event.line.params[1]
        channel = event.line.params[2]
        user = event.line.params[3]
        ip = event.line.params[4]
        host = event.line.params[5]
        server = event.line.params[6]
        nick = event.line.params[7]
        flags = who_flag_parse(event.line.params[8])
        #idle = event.line.params[9]
        account = event.line.params[10]
        gecos = event.line.params[11]

        if nick == '*' or nick not in self.users:
            # *shrug*
            return

        if whoxid not in self.whoxsend:
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

            self.users[nick].chan_status[channel] = mode

        away = flags.away
        operator = flags.operator

        if account == '0':
            # Not logged in
            account = ''

        if ip == '255.255.255.255':
            # Cloaked
            ip = None

        self.users[nick].user = user
        self.users[nick].host = host
        self.users[nick].server = server
        self.users[nick].gecos = gecos
        self.users[nick].away = away
        self.users[nick].operator = operator
        self.users[nick].account = account
        self.users[nick].ip = ip

