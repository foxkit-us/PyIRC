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

from PyIRC.casemapping import IRCDict, IRCDefaultDict, IRCSet
from PyIRC.extension import BaseExtension
from PyIRC.hook import hook
from PyIRC.line import Hostmask
from PyIRC.numerics import Numerics
from PyIRC.auxparse import (mode_parse, prefix_parse, who_flag_parse,
                            status_prefix_parse)


logger = getLogger(__name__)


class User:

    """ A user entity.

    The following attribute is publicly available:

    channels
        Mapping of channels, where the keys are casemapped channel names, and
        the values are their status modes on the channel.

    For more elaborate channel tracking, see channeltrack.ChannelTrack.
    """

    def __init__(self, case, nick, **kwargs):
        """Store the data for a user.

        Unknown values are stored as None, whereas empty ones are stored as
        '' or 0, so take care in comparisons involving values from this class.

        Arguments:

        nick
            Nickname of the user, not casemapped.

        case
            Casemapping to use for channels member.

        Keyword arguments:

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

        # Statuses in channels
        # This assumes case never changes.
        self.channels = IRCDict(case)

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
            if v is None or k in ('k', 'v', 'fmt', 'self'):
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

    requires = ["BasicRFC", "ISupport"]

    def __init__(self, base, **kwargs):
        self.base = base

        self.u_expire_timers = IRCDict(self.base.case)
        self.who_timers = IRCDict(self.base.case)

        self.users = IRCDict(self.base.case)
        self.whois_send = IRCSet(self.base.case)

        # Authentication callbacks
        self.auth_cb = IRCDefaultDict(self.base.case, list)

        # WHOX sent list
        self.whox_send = list()

        # Create ourselves
        basicrfc = self.get_extension("BasicRFC")
        self.add_user(basicrfc.nick, user=self.base.username,
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
        user = self.get_user(nick)
        if not user:
            # Add a user for now, get details later.
            self.users[nick] = User(self.base.case, nick)

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

        Returns None if user not found.

        Arguments:

        nick
            Nickname of the user to retrieve.
        """
        return self.users.get(nick)

    def add_user(self, nick, **kwargs):
        """Add a user to the tracking dictionary.

        Avoid using this method directly unless you know what you are doing.
        """
        user = self.get_user(nick)
        if not user:
            user = User(self.base.case, nick, **kwargs)
            self.users[nick] = user

        return user

    def remove_user(self, nick):
        """Remove a user from the tracking dictionary.

        Avoid using this method directly unless you know what you are doing.
        """
        if nick not in self.users:
            logger.warning("Deleting nonexistent user: %s", nick)
            return

        logger.debug("Deleted user: %s", nick)

        del self.users[nick]

    def timeout_user(self, nick):
        """Time a user out, cancelling existing timeouts

        Avoid using this method directly unless you know what you are doing.
        """
        if nick in self.u_expire_timers:
            self.unschedule(self.u_expire_timers[nick])

        callback = partial(self.remove_user, nick)
        self.u_expire_timers[nick] = self.schedule(30, callback)

    def update_username_host(self, line):
        """Update a user's basic info, based on line hostmask info.

        Avoid using this method directly unless you know what you are doing.
        """
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

    @hook("hooks", "case_change")
    def case_change(self, event):
        case = self.base.case

        self.u_expire_timers = self.u_expire_timers.convert(case)
        self.who_timers = self.who_timers.convert(case)

        self.users = self.users.convert(case)
        self.whois_send = self.whois_send.convert(case)

        self.auth_cb = self.auth_cb.convert(case)

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
        self.update_username_host(event.line)

        user = self.get_user(event.line.hostmask.nick)
        assert user

        user.account = '' if account == '*' else account

        if user.nick in self.auth_cb:
            # User is awaiting authentication
            for callback in self.auth_cb[user.nick]:
                callback(user)

            del self.auth_cb[user.nick]

    @hook("commands", "AWAY")
    def away(self, event):
        self.update_username_host(event.line)

        user = self.get_user(event.line.hostmask.nick)
        assert user

        user.away = bool(event.line.params)

    @hook("commands", "CHGHOST")
    def chghost(self, event):
        # NB - we don't know if a user is cloaking or uncloaking, or changing
        # cloak, so do NOT update user's cloak.
        self.update_username_host(event.line)

        user = self.get_user(event.line.hostmask.nick)
        assert user

        user.username = event.line.params[0]
        user.host = event.line.params[1]

    @hook("commands", "JOIN")
    def join(self, event):
        channel = event.line.params[0]
        nick = event.line.hostmask.nick

        user = self.get_user(nick)
        if user:
            # Remove any pending expiration timer
            self.u_expire_timers.pop(nick, None)
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

        basicrfc = self.get_extension("BasicRFC")
        if self.casecmp(nick, basicrfc.nick):
            # It's us!
            isupport = self.get_extension("ISupport")

            params = [channel]
            if isupport.get("WHOX"):
                # Use WHOX if possible
                num = ''.join(str(randint(0, 9)) for x in range(randint(1, 3)))
                params.append("%tcuihsnflar," + num)
                self.whox_send.append(num)

            sched = self.schedule(2, partial(self.send, "WHO", params))
            self.who_timers[channel] = sched

        # Add the channel
        user.channels[channel] = set

    @hook("commands", "MODE")
    def mode(self, event):
        self.update_username_host(event.line)

        isupport = self.get_extension("ISupport")
        modegroups = list(isupport.get("CHANMODES"))
        prefix = prefix_parse(isupport.get("PREFIX"))

        channel = event.line.params[0]

        # Don't care if user-directed, as that means us most of the time
        if not channel.startswith(isupport.get("CHANTYPES")):
            return

        modes = event.line.params[1]
        if len(event.line.params) >= 3:
            params = event.line.params[2:]
        else:
            params = []
        remove = False
        for mode, nick, adding in mode_parse(modes, params, modegroups,
                                             prefix):
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
        if not cap_negotiate:
            return

        if remove and 'multi-prefix' in cap_negotiate.local:
            # Reissue a names request if we don't have multi-prefix
            self.send("NAMES", [channel])

    @hook("commands", "NICK")
    def nick(self, event):
        self.update_username_host(event.line)

        oldnick = event.line.hostmask.nick
        newnick = event.line.params[0]

        assert self.get_user(oldnick)

        self.users[newnick] = self.get_user(oldnick)
        self.users[newnick].nick = newnick

        del self.users[oldnick]

    @hook("commands", Numerics.ERR_NOSUCHNICK)
    def notfound(self, event):
        nick = event.line.params[1]
        if nick in self.auth_cb:
            # User doesn't exist, call back
            for callback in self.auth_cb[nick]:
                callback(None)

            del self.auth_cb[nick]

        self.remove_user(nick)

    @hook("commands", "PRIVMSG")
    @hook("commands", "NOTICE")
    def message(self, event):
        if event.line.params[0] == '*':
            # We are not registered, do nothing.
            return

        hostmask = event.line.hostmask
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
            # Obtain more information about the user
            user = self.add_user(hostmask.nick, user=hostmask.username,
                                 host=hostmask.host)

            if hostmask.nick not in self.whois_send:
                self.send("WHOIS", ['*', hostmask.nick])
                self.whois_send.add(hostmask.nick)

            self.timeout_user(hostmask.nick)

    @hook("commands", "KICK")
    @hook("commands", "PART")
    def part(self, event):
        channel = event.line.params[0]

        if event.line.command.lower() == 'part':
            user = self.get_user(event.line.hostmask.nick)
        elif event.line.command.lower() == 'kick':
            user = self.get_user(event.line.params[1])
        assert user

        assert channel in user.channels
        del user.channels[channel]

        basicrfc = self.get_extension("BasicRFC")
        if self.casecmp(user.nick, basicrfc.nick):
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
            # No more channels and not us, delete
            # TODO - possible MONITOR support?
            self.remove_user(event.line.hostmask.nick)

    @hook("commands", "QUIT")
    def quit(self, event):
        assert event.line.hostmask.nick in self.users
        self.remove_user(event.line.hostmask.nick)

    @hook("commands", Numerics.RPL_NAMREPLY)
    def names(self, event):
        channel = event.line.params[2]

        isupport = self.get_extension("ISupport")
        prefix = prefix_parse(isupport.get("PREFIX"))

        for nick in event.line.params[-1].split():
            mode, nick = status_prefix_parse(nick, prefix)

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
        if not self.whox_send:
            return

        channel = event.line.params[1]
        del self.who_timers[channel]
        del self.whox_send[0]

    @hook("commands", Numerics.RPL_ENDOFWHOIS)
    def whois_end(self, event):
        nick = event.line.params[1]

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

    @hook("commands", Numerics.RPL_WHOISUSER)
    def whois_user(self, event):
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
        user = self.get_user(event.line.params[1])
        if not user:
            return

        isupport = self.get_extension("ISupport")
        prefix = prefix_parse(isupport.get("PREFIX"))

        for channel in event.line.params[-1].split():
            mode = set()
            mode, channel = status_prefix_parse(channel, prefix)
            user.channels[channel] = mode

    @hook("commands", Numerics.RPL_WHOISHOST)
    def whois_host(self, event):
        user = self.get_user(event.line.params[1])
        if not user:
            return

        # Fucking unreal did this shit.
        string, _, ip = event.line.params[-1].rpartition(' ')
        string, _, realhost = string.rpartition(' ')

        user.ip = ip
        user.realhost = realhost

    @hook("commands", Numerics.RPL_WHOISIDLE)
    def whois_idle(self, event):
        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.signon = int(event.line.params[3])

    @hook("commands", Numerics.RPL_WHOISOPERATOR)
    def whois_operator(self, event):
        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.operator = True

    @hook("commands", Numerics.RPL_WHOISSECURE)
    def whois_secure(self, event):
        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.secure = True

    @hook("commands", Numerics.RPL_WHOISSERVER)
    def whois_server(self, event):
        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.server = event.line.params[2]
        user.server_desc = event.line.params[3]

    @hook("commands", Numerics.RPL_WHOISLOGGEDIN)
    def whois_account(self, event):
        user = self.get_user(event.line.params[1])
        if not user:
            return

        user.account = event.line.params[2]

        nick = user.nick
        if nick in self.auth_cb:
            # User is awaiting authentication
            for callback in self.auth_cb[nick]:
                callback(user)

            del self.auth_cb[nick]

    @hook("commands", Numerics.RPL_WHOREPLY)
    def who(self, event):
        if len(event.line.params) < 8:
            # Some bizarre RFC breaking server
            logger.warn("Malformed WHO from server")
            return

        channel = event.line.params[1]
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

        if isupport.get("RFC2812"):
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
            prefix = prefix_parse(isupport.get("PREFIX"))

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

        user.username = username
        user.host = host
        user.gecos = gecos
        user.away = away
        user.operator = operator
        user.account = account
        user.ip = ip

    @hook("commands", Numerics.RPL_WHOSPCRPL)
    def whox(self, event):
        if len(event.line.params) != 12:
            # Not from us!
            return

        whoxid = event.line.params[1]
        channel = event.line.params[2]
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

            prefix = prefix_parse(isupport.get("PREFIX"))

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

        user.username = username
        user.host = host
        user.server = server
        user.gecos = gecos
        user.away = away
        user.operator = operator
        user.account = account
        user.ip = ip
