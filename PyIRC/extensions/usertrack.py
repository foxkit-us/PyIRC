# Copyright © 2013-2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.

from collections import defaultdict
from random import randint
from functools import partial
from logging import getLogger

from PyIRC.base import BaseExtension
from PyIRC.line import Hostmask
from PyIRC.numerics import Numerics
from PyIRC.mode import mode_parse, prefix_parse


logger = getLogger(__name__)


class User:

    """ A user entity. """

    # There might be a lot of these, so best to use slots
    __slots__ = ["nick", "user", "host", "gecos", "account", "server",
                 "secure", "operator", "chan_status"]

    def __init__(self, nick, **kwargs):
        self.nick = nick
        self.user = kwargs.get("user", None)
        self.host = kwargs.get("host", None)
        self.gecos = kwargs.get("gecos", None)
        self.account = kwargs.get("account", None)
        self.server = kwargs.get("server", None)
        self.secure = kwargs.get("secure", None)
        self.operator = kwargs.get("operator", None)

        # Statuses in channels
        self.chan_status = defaultdict(set)

    def __repr__(self):
        return "User(nick={}, user={}, host={}, gecos={}, account={}, " \
            "server={})".format(self.nick, self.user, self.host, self.gecos,
                                self.account, self.server)


class UserTrack(BaseExtension):

    """ Track various user metrics, such as account info """

    caps = {
        "account-notify" : [],
        "away-notify" : []
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
        self.whoxsend = set()

    def update_user_host(self, line):
        """ Update a user's basic info """

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

            params = ["WHO", channel]
            if "WHOX" in isupport.supported:
                # Use WHOX if possible
                num = ''.join(str(randint(0, 9)) for x in range(randint(1, 3)))
                params.append("%tcuihsnflar,"+num)
                self.whoxset.add(num)

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
        if not channel.startswith(c for c in chantypes):
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

        self.update_user_host(event.line)

        hostmask = event.line.hostmask

        expire = True
        if event.line.hostmask.nick in self.user_expire_timers:
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
            expire_fn = (lambda u : del self.users[u])
            self.user_expire_timers[hostmask.nick] = self.schedule(30,
                partial(expire_fn, hostmask.nick))

    def part(self, event):
        """ Exit a user """

        channel = event.line.params[0]

        assert event.line.hostmask.nick in self.users

        user = self.users[event.line.hostmask.nick]
        assert channel in user.chan_status

        del user.chan_status[channel]

        expire_fn = (lambda u : del self.users[u])

        if event.line.hostmask.nick == self.base.nick:
            # Left the channel, scan all users
            for u_nick, u_user in self.users.items():
                if (channel in u_user.chan_status and
                        len(u_user.chan_status) == 1):
                    # Expire in 30 seconds if they are the only channel we
                    # know about that has them
                    sched = self.schedule(30, partial(expire_fn, u_nick))
                    self.user_expire_timers[u_nick] = sched
        elif not user.chan_status:
            # No more channels and not us, delete in 30 seconds
            sched = self.schedule(30, partial(expire_fn,
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
                mode, user = user[0], user[1:]
                mode.add(pmap[mode])

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

            if mode:
                # Apply modes
                self.users[hostmask.nick].chan_status.update(mode)
