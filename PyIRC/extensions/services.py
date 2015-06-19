#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


""" Utilities for interacting with IRC services """


from logging import getLogger

from PyIRC.extension import BaseExtension
from PyIRC.hook import hook


logger = getLogger(__name__)


class ServicesLogin(BaseExtension):

    """ Support services login.

    Use of this module is discouraged. Use the SASL module if at all
    possible. It is not possible to know if our authentication was
    a success or failure, because services may use any string to report
    back authentication results, and they are often localised depending on
    IRC network.

    It also creates a security hole, as you can never be 100% sure who or
    what you're talking to (though some networks support a full nick!user@host
    in the target to message a user). This makes password disclosure much more
    likely.

    This extension adds ``base.services_login` as itself as an alias for
    ``get_extension("ServicesLogin").``.
    """

    def __init__(self, *args, **kwargs):
        """ Initalise the ServicesLogin extension.

        :key services_username:
            The username to use for authentication.

        :key services_password:
            The password to use for authentication.

        :key services_idenitfy_fmt:
            A format string using {username} and {password} to send the
            correct message to services.

        :key services_bot:
            The user to send authentication to (defaults to NickServ). Can be
            a full nick!user@host set for the networks that support or require
            this mechanism.

        :key services_command:
            Command to use to authenticate. Defaults to PRIVMSG, but
            NS/NICKSERV are recommended for networks that support it for some
            improved security.
        """
        super().__init__(*args, **kwargs)

        self.base.services_login = self

        self.username = kwargs.get("services_username", self.nick)
        self.password = kwargs.get("services_password")

        # Usable with atheme and probably anope
        self.identify = kwargs.get("services_identify_fmt",
                                   "IDENTIFY {username} {password}")

        self.services_bot = kwargs.get("services_bot", "NickServ")
        self.services_command = kwargs.get("services_command", "PRIVMSG")

        # Cache format string
        self.identify = self.identify.format(username=self.username,
                                             password=self.password)

        self.authenticated = False

    @hook("commands", "NOTICE")
    @hook("commands", "PRIVMSG")
    def authenticate(self, event):
        if self.password is None:
            return

        if self.authenticated or not self.registered:
            return

        logger.debug("Authenticating to services bot %s with username %s",
                     self.services_bot, self.username)

        if self.services_command.lower() in ("PRIVMSG", "NOTICE"):
            self.send(self.services_command, [self.services_bot,
                                              self.identify])
        else:
            # XXX assuming self.services_bot is unused is probably not wise.
            # Seems okay for now though.
            self.send(self.services_command, [self.identify])

        # And STAY out! ;)
        self.authenticated = True
