# Copyright © 2013-2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Track users we have seen and their associated data

Tracks users we know about, whether on channels or through private messages.
Maintains state such as nicknames, channel statuses, away status, and the
like.
"""


from itertools import chain
from random import randint
from functools import partial
from collections import defaultdict
from logging import getLogger

from PyIRC.extension import BaseExtension, hook
from PyIRC.line import Hostmask
from PyIRC.numerics import Numerics
from PyIRC.auxparse import mode_parse, prefix_parse, who_flag_parse


logger = getLogger(__name__)


class User:

    """ A user entity.

    The following attribute is publicly available:

    channels
        Mapping of channels, where the keys are casemapped channel names, and
        the values are their status modes on the channel.

    For more elaborate channel tracking, see channeltrack.ChannelTrack.
    """

    def __init__(self, nick, **kwargs):
        """Store the data for a user.

        Unknown values are stored as None, whereas empty ones are stored as
        '' or 0, so take care in comparisons involving values from this class.

        Keyword arguments:

        nick
            Nickname of the user, not casemapped.

        username
            Username of the user, or ident (depending on IRC daemon).

        host
            Hostname of the user. May be fake due to a cloak.

        gecos
            The GECOS (aka "real name") of a user. Usually just freeform data
            of dubious usefulness.

        account
            Services account name of the user.

        server
            Server the user is on. Not always reliable or present.

        secure
            User is using SSL. Always assume unsecured unless set to True.

        operator
            User is an operator. Being set to None does not guarantee a user
            is not an operator due to IRC daemon limitations and data hiding.

        signon
            Signon time for the user. May not be set.

        ip
            IP for the user reported from the server. May be bogus and likely
            nonexistent on networks with host cloaking.

        realhost
            Real hostname for a user. Probably not present in most cases.
        """
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
        self.channels = dict()

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

    """ Track various user metrics, such as account info, and some channel
    tracking.

    The following attribute is publlicly available:

    users
        Mapping of users, where the keys are casemapped nicks, and values are
        User instances.
    """

    caps = {
        "account-notify" : [],
        "away-notify" : [],
        "chghost" : [],
        "extended-join" : [],
        "multi-prefix" : [],
        "userhost-in-names" : [],
    }

    requires = ["ISupport"]

    def __init__(self, base, **kwargs):
        self.base = base

        self.u_expire_timers = dict()
        self.who_timers = dict()

        self.users = dict()
        self.whox_send = list()
        self.whois_send = set()

        # Authentication callbacks
        self.auth_cb = defaultdict(list)

        # Create ourselves
        self.add_user(self.base.nick, user=self.base.username,
                      gecos=self.base.gecos)

    def authenticate(self, nick, callback):
        """Get authentication for a user and return result in a callback

        Arguments:

        nick
            Nickname of user to check authentication for

        callback
            Callback to call for user when authentication is discovered. The
            User instance is passed in as the first parameter, or None if the
            user is not found. Use functools.partial to pass other arguments.
        """
        fold_nick = self.casefold(user.nick)

        user = self.get_user(nick)
        if not user:
            # Add a user for now, get details later.
            self.users[fold_nick] = User(nick)

        if user.account is not None:
            # User account is known
            callback(user)
        elif fold_nick not in self.whois_send:
            # Defer for a whois
            self.auth_cb[fold_nick].append(callback)
            self.send("WHOIS", ["*", user.nick])
            self.whois_send.add(fold_nick)

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

        # Update
        user.nick = hostmask.nick

        if hostmask.username:
            user.username = hostmask.username

        if hostmask.host:
            user.host = hostmask.host

    @hook("hooks", "disconnected")
    def close(self, event):
        timers = chain(self.u_expire_timers.values(),
                       self.who_timers.values())
        for timer in timers:
            try:
                self.unschedule(timer)
            except ValueError:
                pass

        self.users.clear()
        self.whox_send.clear()

    @hook("commands", "ACCOUNT")
    def account(self, event):
        """ Get account changes """

        self.update_username_host(event.line)

        user = self.get_user(event.line.hostmask.nick)
        assert user

        user.account = '' if account == '*' else account

        nick = self.casefold(user.nick)
        if nick in self.auth_cb:
            # User is awaiting authentication
            for callback in self.auth_cb[nick]:
                callback(user)

            del self.auth_cb[nick]

    @hook("commands", "AWAY")
    def away(self, event):
        """ Get away status changes """

        self.update_username_host(event.line)

        user = self.get_user(event.line.hostmask.nick)
        assert user

        user.away = bool(event.line.params)

    @hook("commands", "CHGHOST")
    def chghost(self, event):
        """ Update a user's host """

        self.update_username_host(event.line)

        user = self.get_user(event.line.hostmask.nick)
        assert user

        user.username = event.line.params[0]
        user.host = event.line.params[1]

    @hook("commands", "JOIN")
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
                params.append("%tcuihsnflar," + num)
                self.whox_send.append(num)

            sched = self.schedule(2, partial(self.send, "WHO", params))
            self.who_timers[self.casefold(channel)] = sched

        # Add the channel
        user.channels[self.casefold(channel)] = set()

    @hook("commands", "MODE")
    def mode(self, event):
        """ Got a channel mode """

        self.update_username_host(event.line)

        isupport = self.get_extension("ISupport")
        chantypes = isupport.supported.get("CHANTYPES", '#+!&')
        modegroups = list(isupport.supported.get("CHANMODES",
                                                 ["b", "k", "l", "imnstp"]))

        prefix = prefix_parse(isupport.supported.get("PREFIX", "(ov)@+"))

        # Parse prefixes like list modes
        modegroups[0] += ''.join(prefix.keys())

        channel = self.casefold(event.line.params[0])

        # Don't care if user-directed, as that means us most of the time
        if not channel.startswith(*chantypes):
            return

        modes = event.line.params[1]
        if len(event.line.params) >= 3:
            params = event.line.params[2:]
        else:
            params = []
        remove = False
        for mode, nick, adding in mode_parse(modes, params, modegroups):
            if mode not in prefix:
                continue

            user = self.get_user(nick)
            if not user:
                logger.warn("IRC server sent us mode %s for nonexistent " \
                            "user: %s", mode, user)
                continue

            if adding:
                channel = user.channels[channel]
                channel.update(mode)
                logger.debug("Adding mode for nick %s: %s", user.nick, mode)
            else:
                channel = user.channels[channel]
                channel.difference_update(mode)
                logger.debug("Deleting mode for nick %s: %s", user.nick, mode)
                remove = True

        cap_negotiate = self.get_extension("CapNegotiate")
        if remove and not (cap_negotiate and 'multi-prefix' in
                           cap_negotiate.local):
            # Reissue a names request if we don't have multi-prefix
            self.send("NAMES", [channel])

    @hook("commands", "NICK")
    def nick(self, event):
        """ User changed nick """

        self.update_username_host(event.line)

        oldnick = event.line.hostmask.nick
        newnick = event.line.params[0]

        assert self.get_user(oldnick)

        self.users[self.casefold(newnick)] = self.get_user(oldnick)
        self.users[self.casefold(newnick)].nick = newnick

        del self.users[self.casefold(oldnick)]

    @hook("commands", Numerics.ERR_NOSUCHNICK)
    def notfound(self, event):
        """ User is gone """

        nick = self.casefold(event.line.params[1])
        if nick in self.auth_cb:
            # User doesn't exist, call back
            for callback in self.auth_cb[nick]:
                callback(None)

            del self.auth_cb[nick]

        self.remove_user(nick)

    @hook("commands", "PRIVMSG")
    @hook("commands", "NOTICE")
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

            if self.casefold(hostmask.nick) not in self.whois_send:
                self.send("WHOIS", ['*', hostmask.nick])
                self.whois_send.add(self.casefold(hostmask.nick))

            self.timeout_user(hostmask.nick)

    @hook("commands", "KICK")
    @hook("commands", "PART")
    def part(self, event):
        """ Exit a user """

        channel = self.casefold(event.line.params[0])

        if event.line.command.lower() == 'part':
            user = self.get_user(event.line.hostmask.nick)
        elif event.line.command.lower() == 'kick':
            user = self.get_user(event.line.params[1])
        assert user

        assert channel in user.channels
        del user.channels[channel]

        if (self.casefold(user.nick) == self.casefold(self.base.nick)):
            # We left the channel, scan all users to remove unneeded ones
            for u_nick, u_user in list(self.users.items()):
                if channel in u_user.channels:
                    # Purge from the cache since we don't know for certain.
                    del u_user.channels[channel]

                if self.casefold(u_nick) == self.casefold(self.base.nick):
                    # Don't delete ourselves!
                    continue

                if not u_user.channels:
                    # Delete the user outright to purge any cached data
                    # The data must be considered invalid when we leave
                    # TODO - possible MONITOR support?
                    self.remove_user(u_nick)
                    continue

        elif not user.channels:
            # No more channels and not us, delete
            # TODO - possible MONITOR support?
            self.remove_user(event.line.hostmask.nick)

    @hook("commands", "QUIT")
    def quit(self, event):
        """ Exit a user for real """

        assert self.casefold(event.line.hostmask.nick) in self.users
        self.remove_user(event.line.hostmask.nick)

    @hook("commands", Numerics.RPL_NAMREPLY)
    def names(self, event):
        """ Process a channel NAMES event """

        channel = self.casefold(event.line.params[2])

        isupport = self.get_extension("ISupport")
        prefix = prefix_parse(isupport.supported.get("PREFIX", "(ov)@+"))
        pmap = {v : k for k, v in prefix.items()}

        for nick in event.line.params[-1].split():
            mode = set()
            while nick[0] in pmap:
                # Accomodate multi-prefix
                prefix, nick = nick[0], nick[1:]
                mode.add(pmap[prefix])

            # userhost-in-names (no need to check, nick goes through this
            # just fine)
            hostmask = Hostmask.parse(nick)
            username = hostmask.username if hostmask.username else None
            host = hostmask.host if hostmask.host else None

            user = self.get_user(nick)
            if user:
                # Update user info
                if username:
                    user.username = username

                if host:
                    user.host = host
            else:
                user = self.add_user(nick, user=username, host=host)

            # Apply modes
            if channel in user.channels:
                user.channels[channel].update(mode)
            else:
                user.channels[channel] = mode

    @hook("commands", Numerics.RPL_ENDOFWHO)
    def who_end(self, event):
        """ Process end of WHO reply """

        if not self.whox_send:
            return

        channel = self.casefold(event.line.params[1])
        del self.who_timers[channel]
        del self.whox_send[0]

    @hook("commands", Numerics.RPL_ENDOFWHOIS)
    def whois_end(self, event):
        """ Process end of WHOIS """

        nick = self.casefold(event.line.params[1])

        self.whois_send.discard(nick)

        user = self.get_user(nick)
        if nick in self.auth_cb:
            # User is awaiting authentication
            for callback in self.auth_cb[nick]:
                callback(user)

            del self.auth_cb[nick]

    @hook("commands", Numerics.RPL_WHOISUSER)
    def whois_user(self, event):
        """ The nickname/user/host/gecos of a user """

        nick = event.line.params[1]
        username = event.line.params[2]
        host = event.line.params[3]
        gecos = event.line.params[5]

        user = self.get_user(nick)
        if not user:
            return

        user.nick = nick
        user.username = username
        user.host = host
        user.gecos = gecos

    @hook("commands", Numerics.RPL_WHOISCHANNELS)
    def whois_channels(self, event):
        """ Channels user is on from WHOIS """

        user = self.get_user(event.line.params[1])
        if not user:
            return

        isupport = self.get_extension("ISupport")
        prefix = prefix_parse(isupport.supported.get("PREFIX", "(ov)@+"))
        pmap = {v : k for k, v in prefix.items()}

        for channel in event.line.params[-1].split():
            mode = set()
            while user[0] in pmap:
                # Accomodate multi-prefix
                prefix, user = user[0], user[1:]
                mode.add(pmap[prefix])

            user.channels[self.casefold(channel)] = mode

    @hook("commands", Numerics.RPL_WHOISHOST)
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

    @hook("commands", Numerics.RPL_WHOISIDLE)
    def whois_idle(self, event):
        """ Idle and signon time for user from WHOIS  """

        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.signon = event.line.params[3]

    @hook("commands", Numerics.RPL_WHOISOPERATOR)
    def whois_operator(self, event):
        """ User is an operator according to WHOIS """

        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.operator = True

    @hook("commands", Numerics.RPL_WHOISSECURE)
    def whois_secure(self, event):
        """ User is known to be using SSL from WHOIS """

        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.secure = True

    @hook("commands", Numerics.RPL_WHOISSERVER)
    def whois_server(self, event):
        """ Server the user is logged in on from WHOIS """

        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.server = event.line.params[2]
        user.server_desc = event.line.params[3]

    @hook("commands", Numerics.RPL_WHOISLOGGEDIN)
    def whois_account(self, event):
        """ Services account name of user according to WHOIS """

        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.account = event.line.params[2]

        nick = self.casefold(user.nick)
        if nick in self.auth_cb:
            # User is awaiting authentication
            for callback in self.auth_cb[nick]:
                callback(user)

            del self.auth_cb[nick]

    @hook("commands", Numerics.RPL_WHOREPLY)
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
            prefix = prefix_parse(isupport.supported.get("PREFIX", "(ov)@+"))
            pmap = {v : k for k, v in prefix.items()}

            mode = set()
            for m in flags.modes:
                m = pmap.get(m)
                if m is not None:
                    mode.add(m)

            user.channels[channel] = mode

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

    @hook("commands", Numerics.RPL_WHOSPCRPL)
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
        # idle = event.line.params[9]
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

            prefix = prefix_parse(isupport.supported.get("PREFIX", "(ov)@+"))
            pmap = {v : k for k, v in prefix.items()}

            mode = set()
            for m in flags.modes:
                m = pmap.get(m)
                if m is not None:
                    mode.add(m)

            user.channels[channel] = mode

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
