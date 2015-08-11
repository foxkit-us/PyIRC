# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""IRC daemon-specific routines.

This is the abstract implementation from which all others derive.

"""

import abc

from logging import getLogger

from PyIRC.extensions import BaseExtension


_logger = getLogger(__name__)


class BaseServer(BaseExtension, metaclass=abc.ABCMeta):

    def provides(base):
        """Returns whether or not this extension can provide for the
        server."""
        return False

    def extban_parse(self, string):
        """Parse an extban.

        This is not supported by all IRC daemons.

        :param string:
            String to parse

        :returns:
            An :py:class:`~PyIRC.extensions.ircd.Extban` instance.
        """
        raise NotImplementedError("Extbans are not supported.")

    @abc.abstractmethod
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
        raise NotImplementedError

    @abc.abstractmethod
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
        raise NotImplementedError

    @abc.abstractmethod
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
        raise NotImplementedError

    @abc.abstractmethod
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
        raise NotImplementedError

    @abc.abstractmethod
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
        raise NotImplementedError

    @abc.abstractmethod
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
        raise NotImplementedError

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
        raise NotImplementedError("Server does not support GECOS bans.")

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
        raise NotImplementedError("Server does not support GECOS bans.")
    
    @abc.abstractmethod
    def stats_global_ban(self):
        """Get a list of all global bans (often referred to as "g:lines" or,
        confusingly, as "k:lines").

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def stats_server_ban(self, server):
        """Get a list of all server bans (often referred to as "k:lines").

        :param server:
            Server to get the list of bans on.

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def stats_global_ip_ban(self):
        """Get a list of all global IP bans (often referred to as "z:lines" or
        "d:lines").

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """
        raise NotImplementedError

    @abc.abstractmethod
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
        raise NotImplementedError
    
    @abc.abstractmethod
    def stats_global_nickchan_ban(self):
        """Get a list of all global nick/channel bans (often referred to as
        "Q:lines" or "resvs").

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """
        raise NotImplementedError

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
        raise NotImplementedError
    
    def stats_global_gecos_ban(self):
        """Get a list of all global GECOS bans (often referred to as "sglines",
        "n:lines", or "x:lines").

        ..note::
            This may not be implemented on some servers, restricted, or even
            filtered. Unless you are an operator, take the information that is
            returned with a grain of salt.
        """
        raise NotImplementedError

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
        raise NotImplementedError

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
        raise NotImplementedError("Server does not support listing operators.""")

    @abc.abstractmethod
    def stats_uptime(self, server=None):
        """Get the uptime of the server.

        :param server:
            Server to get the uptime of. ``None`` defaults to the current server.
        """
        raise NotImplementedError
