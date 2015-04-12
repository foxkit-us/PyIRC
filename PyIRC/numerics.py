# Copyright © 2013-2015 Elizabeth Myers.  All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Numerics for IRC servers.

This list was generated automatically using techniques that scraped the server
software for them. This work was originally done for the IRCv3 project, but
has been commandeered for this use.

It is believed this covers over 99% of all numerics in actual real-world
usage (no exaggeration :).

There may be aliases as a result of the process. It is recommended to avoid
these aliases, and to use the most common name for the numeric.

Note that not all numerics may be documented, and it may be too difficult to
ever fully document them all. The most common ones will have at least some
attempt to document them.

The following IRC servers or standards were checked:

- Bahamut (2.0.7)
- Charybdis (3.5.0)
- ircd-hybrid (7.0)
- Inspircd (2.0)
- IRCNet ircd (2.11.2)
- ircd-seven (1.1.3)
- ircu (2.10.12.14)
- plexus
- ircd-ratbox (3.0.8)
- RFC1459
- RFC2812
- snircd (1.3.4a)
- UnrealIRCD (3.2.10.4)
"""


# This file has been automatically generated with conflicts manually sorted
out
# The comments show the place the numerics came from
# TODO: fix name duplication

try:
    from enum import Enum
except ImportError:
    from PyIRC.util.enum import Enum


class Numerics(enum.Enum):
    """Numerics used by IRC servers.

    If anything can illustrate IRC's severe fragmentation problem and long
    history of dubious forks, politics, and not-invented-here syndrome, it is
    this enum.
    """

    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_WELCOME = "001"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_YOURHOST = "002"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_YOURHOSTIS = "002"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_CREATED = "003"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_SERVERCREATED = "003"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_MYINFO = "004"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_SERVERVERSION = "004"


    """

     This numeric can be found in:
    - RFC2812
    """
    RPL_BOUNCE_RFC2812 = "005"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - snircd
    - UnrealIRCD
    """
    RPL_ISUPPORT = "005"


    """

     This numeric can be found in:
    - Inspircd
    - UnrealIRCD
    """
    RPL_MAP_UNREAL = "006"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_ENDMAP_UNREAL = "007"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_MAPEND_UNREAL = "007"


    """

     This numeric can be found in:
    - Charybdis
    - Inspircd
    - ircd-seven
    - ircu
    - snircd
    - UnrealIRCD
    """
    RPL_SNOMASK = "008"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_SNOMASKIS = "008"


    """

     This numeric can be found in:
    - IRCNet ircd
    """
    RPL_BOUNCE = "010"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    - UnrealIRCD
    """
    RPL_REDIR = "010"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - snircd
    """
    RPL_MAP = "015"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - snircd
    """
    RPL_MAPMORE = "016"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - snircd
    """
    RPL_MAPEND = "017"


    """

     This numeric can be found in:
    - IRCNet ircd
    """
    RPL_MAPSTART = "018"


    """

     This numeric can be found in:
    - IRCNet ircd
    """
    RPL_HELLO = "020"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_APASSWARN_SET = "030"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_APASSWARN_SECRET = "031"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_APASSWARN_CLEAR = "032"


    """

     This numeric can be found in:
    - ircd-hybrid
    - IRCNet ircd
    - plexus
    """
    RPL_YOURID = "042"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_YOURUUID = "042"


    """

     This numeric can be found in:
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    """
    RPL_SAVENICK = "043"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_REMOTEISUPPORT = "105"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_TRACELINK = "200"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_TRACECONNECTING = "201"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_TRACEHANDSHAKE = "202"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_TRACEUNKNOWN = "203"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_TRACEOPERATOR = "204"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_TRACEUSER = "205"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_TRACESERVER = "206"


    """

     This numeric can be found in:
    - plexus
    """
    RPL_TRACECAPTURED = "207"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC2812
    - UnrealIRCD
    """
    RPL_TRACESERVICE = "207"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_TRACENEWTYPE = "208"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_TRACECLASS = "209"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_STATSHELP = "210"


    """

     This numeric can be found in:
    - RFC2812
    """
    RPL_TRACERECONNECT = "210"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_STATSLINKINFO = "211"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_STATSCOMMANDS = "212"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_STATSCLINE = "213"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    """
    RPL_STATSNLINE = "214"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_STATSOLDNLINE = "214"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_STATSILINE = "215"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_STATSKLINE = "216"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_STATSPLINE_IRCU = "217"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_STATSQLINE = "217"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_STATSYLINE = "218"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ENDOFSTATS = "219"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_STATSBLINE_UNREAL = "220"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_STATSPLINE = "220"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_UMODEIS = "221"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_SQLINE_NICK = "222"


    """

     This numeric can be found in:
    - Bahamut
    """
    RPL_STATSBLINE_BAHAMUT = "222"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_STATSJLINE = "222"


    """

     This numeric can be found in:
    - Bahamut
    """
    RPL_STATSELINE_BAHAMUT = "223"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_STATSGLINE_UNREAL = "223"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_STATSFLINE = "224"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_STATSTLINE_UNREAL = "224"


    """

     This numeric can be found in:
    - Bahamut
    """
    RPL_STATSCLONE = "225"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_STATSDLINE = "225"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_STATSELINE_UNREAL = "225"


    """

     This numeric can be found in:
    - ircd-hybrid
    - ircu
    - plexus
    - snircd
    """
    RPL_STATSALINE = "226"


    """

     This numeric can be found in:
    - Bahamut
    """
    RPL_STATSCOUNT = "226"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_STATSNLINE_UNREAL = "226"


    """

     This numeric can be found in:
    - plexus
    """
    RPL_STATSBLINE_PLEXUS = "227"


    """

     This numeric can be found in:
    - Bahamut
    """
    RPL_STATSGLINE_BAHAMUT = "227"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_STATSVLINE_UNREAL = "227"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_STATSBANVER = "228"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_STATSQLINE_IRCU = "228"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_STATSSPAMF = "229"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_STATSEXCEPTTKL = "230"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_SERVICEINFO = "231"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC1459
    - RFC2812
    """
    RPL_ENDOFSERVICES = "232"


    """

     This numeric can be found in:
    - Inspircd
    - UnrealIRCD
    """
    RPL_RULES = "232"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_SERVICE = "233"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_SERVLIST = "234"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_SERVLISTEND = "235"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_STATSVERBOSE = "236"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_STATSENGINE = "237"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_STATSFLINE_IRCU = "238"


    """

     This numeric can be found in:
    - IRCNet ircd
    """
    RPL_STATSIAUTH = "239"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC2812
    """
    RPL_STATSVLINE = "240"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_STATSLLINE = "241"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_STATSUPTIME = "242"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_STATSOLINE = "243"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_STATSHLINE = "244"


    """

     This numeric can be found in:
    - RFC2812
    """
    RPL_STATSSLINE_RFC2812 = "244"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - plexus
    - ircd-ratbox
    - UnrealIRCD
    """
    RPL_STATSSLINE = "245"


    """

     This numeric can be found in:
    - ircd-hybrid
    """
    RPL_STATSTLINE_HYBRID = "245"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC2812
    """
    RPL_STATSPING = "246"


    """

     This numeric can be found in:
    - ircd-hybrid
    """
    RPL_STATSSERVICE = "246"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_STATSTLINE_IRCU = "246"


    """

     This numeric can be found in:
    - Bahamut
    """
    RPL_STATSULINE_BAHAMUT = "246"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC2812
    """
    RPL_STATSBLINE_RFC2812 = "247"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_STATSGLINE_IRCU = "247"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    - UnrealIRCD
    """
    RPL_STATSXLINE = "247"


    """

     This numeric can be found in:
    - IRCNet ircd
    """
    RPL_STATSDEFINE = "248"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - snircd
    - UnrealIRCD
    """
    RPL_STATSULINE = "248"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - snircd
    - UnrealIRCD
    """
    RPL_STATSDEBUG = "249"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - snircd
    - UnrealIRCD
    """
    RPL_STATSCONN = "250"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC2812
    """
    RPL_STATSDLINE_RFC2812 = "250"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_LUSERCLIENT = "251"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_LUSEROP = "252"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_LUSERUNKNOWN = "253"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_LUSERCHANNELS = "254"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_LUSERME = "255"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ADMINME = "256"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ADMINLOC1 = "257"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ADMINLOC2 = "258"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ADMINEMAIL = "259"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-seven
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_TRACELOG = "261"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_ENDOFTRACE = "262"


    """

     This numeric can be found in:
    - IRCNet ircd
    - ircu
    - RFC2812
    - snircd
    """
    RPL_TRACEEND = "262"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_LOAD2HI = "263"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC2812
    """
    RPL_TRYAGAIN = "263"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - plexus
    - ircd-ratbox
    - UnrealIRCD
    """
    RPL_LOCALUSERS = "265"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - plexus
    - ircd-ratbox
    - UnrealIRCD
    """
    RPL_GLOBALUSERS = "266"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_MAPUSERS = "270"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircu
    - snircd
    """
    RPL_PRIVS = "270"


    """

     This numeric can be found in:
    - Bahamut
    - ircu
    - snircd
    - UnrealIRCD
    """
    RPL_SILELIST = "271"


    """

     This numeric can be found in:
    - Bahamut
    - ircu
    - snircd
    - UnrealIRCD
    """
    RPL_ENDOFSILELIST = "272"


    """

     This numeric can be found in:
    - ircu
    - snircd
    - UnrealIRCD
    """
    RPL_STATSDLINE_IRCU = "275"


    """

     This numeric can be found in:
    - Bahamut
    """
    RPL_USINGSSL = "275"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_STATSRLINE = "276"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    """
    RPL_WHOISCERTFP = "276"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_GLIST = "280"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_ACCEPTLIST = "281"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_ENDOFGLIST = "281"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_ENDOFACCEPT = "282"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_JUPELIST = "282"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_ENDOFJUPELIST = "283"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_FEATURE = "284"


    """

     This numeric can be found in:
    - ircd-hybrid
    - snircd
    """
    RPL_NEWHOSTIS = "285"


    """

     This numeric can be found in:
    - snircd
    """
    RPL_CHKHEAD = "286"


    """

     This numeric can be found in:
    - snircd
    """
    RPL_CHANUSER = "287"


    """

     This numeric can be found in:
    - snircd
    """
    RPL_PATCHHEAD = "288"


    """

     This numeric can be found in:
    - snircd
    """
    RPL_PATCHCON = "289"


    """

     This numeric can be found in:
    - snircd
    """
    RPL_DATASTR = "290"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_HELPHDR = "290"


    """

     This numeric can be found in:
    - snircd
    """
    RPL_ENDOFCHECK = "291"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_HELPOP = "291"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_HELPTLR = "292"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_HELPHLP = "293"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_HELPFWD = "294"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_HELPIGN = "295"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_NONE = "300"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_AWAY = "301"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_USERHOST = "302"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ISON = "303"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_SYNTAX = "304"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - plexus
    - ircd-ratbox
    - snircd
    - UnrealIRCD
    """
    RPL_TEXT = "304"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_UNAWAY = "305"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_NOWAWAY = "306"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - plexus
    - UnrealIRCD
    """
    RPL_WHOISREGNICK = "307"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_RULESSTART = "308"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_RULESTART = "308"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    """
    RPL_WHOISADMIN = "308"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_ENDOFRULES = "309"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_RULESEND = "309"


    """

     This numeric can be found in:
    - Bahamut
    """
    RPL_WHOISSADMIN = "309"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_WHOISHELPOP = "310"


    """

     This numeric can be found in:
    - ircd-hybrid
    - plexus
    """
    RPL_WHOISMODES = "310"


    """

     This numeric can be found in:
    - Bahamut
    """
    RPL_WHOISSVCMSG = "310"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_WHOISUSER = "311"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_WHOISSERVER = "312"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_WHOISOPERATOR = "313"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_WHOWASUSER = "314"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ENDOFWHO = "315"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_WHOISCHANOP = "316"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_WHOISIDLE = "317"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ENDOFWHOIS = "318"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_WHOISCHANNELS = "319"


    """

     This numeric can be found in:
    - ircd-seven
    - UnrealIRCD
    """
    RPL_WHOISSPECIAL = "320"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_LISTSTART = "321"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_LIST = "322"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_LISTEND = "323"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_CHANNELMODEIS = "324"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    """
    RPL_CHANNELMLOCK = "325"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC2812
    """
    RPL_UNIQOPIS = "325"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    """
    RPL_CHANNELURL = "328"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_CHANNELCREATED = "329"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - snircd
    - UnrealIRCD
    """
    RPL_CREATIONTIME = "329"


    """

     This numeric can be found in:
    - ircd-hybrid
    - ircu
    - snircd
    """
    RPL_WHOISACCOUNT = "330"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircd-ratbox
    - UnrealIRCD
    """
    RPL_WHOISLOGGEDIN = "330"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_NOTOPIC = "331"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_NOTOPICSET = "331"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_TOPIC = "332"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_TOPICTIME = "333"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - snircd
    - UnrealIRCD
    """
    RPL_TOPICWHOTIME = "333"


    """

     This numeric can be found in:
    - IRCNet ircd
    """
    RPL_TOPIC_WHO_TIME = "333"


    """

     This numeric can be found in:
    - Bahamut
    """
    RPL_COMMANDSYNTAX = "334"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_LISTSYNTAX = "334"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_LISTUSAGE = "334"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_WHOISBOT = "335"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_INVITELIST_UNREAL_OLD = "336"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_ENDOFINVITELIST_UNREAL_OLD = "337"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    """
    RPL_WHOISTEXT = "337"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - snircd
    """
    RPL_WHOISACTUALLY = "338"


    """

     This numeric can be found in:
    - ircu
    - snircd
    - UnrealIRCD
    """
    RPL_USERIP = "340"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_INVITING = "341"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_SUMMONING = "342"


    """

     This numeric can be found in:
    - snircd
    """
    RPL_WHOISOPERNAME = "343"


    """

     This numeric can be found in:
    - IRCNet ircd
    """
    RPL_REOPLIST = "344"


    """

     This numeric can be found in:
    - IRCNet ircd
    """
    RPL_ENDOFREOPLIST = "345"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_INVITED = "345"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_ISSUEDINVITE = "345"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_INVEXLIST = "346"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC2812
    - snircd
    """
    RPL_INVITELIST = "346"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_ENDOFINVEXLIST = "347"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC2812
    - snircd
    """
    RPL_ENDOFINVITELIST = "347"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - plexus
    - ircd-ratbox
    - RFC2812
    """
    RPL_EXCEPTLIST = "348"


    """

     This numeric can be found in:
    - Bahamut
    """
    RPL_EXEMPTLIST = "348"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_EXLIST = "348"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - plexus
    - ircd-ratbox
    - RFC2812
    """
    RPL_ENDOFEXCEPTLIST = "349"


    """

     This numeric can be found in:
    - Bahamut
    """
    RPL_ENDOFEXEMPTLIST = "349"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_ENDOFEXLIST = "349"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_VERSION = "351"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_WHOREPLY = "352"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_NAMREPLY = "353"


    """

     This numeric can be found in:
    - Bahamut
    """
    RPL_RWHOREPLY = "354"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircu
    - snircd
    """
    RPL_WHOSPCRPL = "354"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    RPL_DELNAMREPLY = "355"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    """
    RPL_WHOWASREAL = "360"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_KILLDONE = "361"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_CLOSING = "362"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_CLOSEEND = "363"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_LINKS = "364"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ENDOFLINKS = "365"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ENDOFNAMES = "366"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_BANLIST = "367"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ENDOFBANLIST = "368"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ENDOFWHOWAS = "369"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_INFO = "371"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_MOTD = "372"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_INFOSTART = "373"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ENDOFINFO = "374"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_MOTDSTART = "375"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_ENDOFMOTD = "376"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - UnrealIRCD
    """
    RPL_WHOISHOST = "378"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_WHOISMODES_UNREAL = "379"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_YOUAREOPER = "381"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_YOUREOPER = "381"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_REHASHING = "382"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC2812
    - UnrealIRCD
    """
    RPL_YOURESERVICE = "383"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_MYPORTIS = "384"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    - UnrealIRCD
    """
    RPL_NOTOPERANYMORE = "385"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_QLIST = "386"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_RSACHALLENGE = "386"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_ENDOFQLIST = "387"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_ALIST = "388"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_ENDOFALIST = "389"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    RPL_TIME = "391"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_USERSSTART = "392"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_USERS = "393"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_ENDOFUSERS = "394"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    RPL_NOUSERS = "395"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircu
    - snircd
    """
    RPL_HOSTHIDDEN = "396"


    """

     This numeric can be found in:
    - plexus
    """
    RPL_VISIBLEHOST = "396"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_YOURDISPLAYEDHOST = "396"


    """

     This numeric can be found in:
    - snircd
    """
    RPL_STATSSLINE_SNIRCD = "398"


    """

     This numeric can be found in:
    - snircd
    """
    RPL_USINGSLINE = "399"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NOSUCHNICK = "401"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NOSUCHSERVER = "402"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NOSUCHCHANNEL = "403"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_CANNOTSENDTOCHAN = "404"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_TOOMANYCHANNELS = "405"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_WASNOSUCHNICK = "406"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_TOOMANYTARGETS = "407"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - plexus
    """
    ERR_NOCTRLSONCHAN = "408"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC2812
    - UnrealIRCD
    """
    ERR_NOSUCHSERVICE = "408"


    """

     This numeric can be found in:
    - snircd
    """
    ERR_SEARCHNOMATCH = "408"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NOORIGIN = "409"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    - UnrealIRCD
    """
    ERR_INVALIDCAPCMD = "410"


    """

     This numeric can be found in:
    - Inspircd
    """
    ERR_INVALIDCAPSUBCOMMAND = "410"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_UNKNOWNCAPCMD = "410"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NORECIPIENT = "411"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NOTEXTTOSEND = "412"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NOTOPLEVEL = "413"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_WILDTOPLEVEL = "414"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC2812
    """
    ERR_BADMASK = "415"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_QUERYTOOLONG = "416"


    """

     This numeric can be found in:
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    """
    ERR_TOOMANYMATCHES = "416"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_INPUTTOOLONG = "417"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_UNKNOWNCOMMAND = "421"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NOMOTD = "422"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NOADMININFO = "423"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    ERR_FILEERROR = "424"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_NOOPERMOTD = "425"


    """

     This numeric can be found in:
    - Bahamut
    - UnrealIRCD
    """
    ERR_TOOMANYAWAY = "429"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NONICKNAMEGIVEN = "431"


    """

     This numeric can be found in:
    - IRCNet ircd
    """
    ERR_ERRONEOUSNICKNAME = "432"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_ERRONEUSNICKNAME = "432"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NICKNAMEINUSE = "433"


    """

     This numeric can be found in:
    - Inspircd
    - UnrealIRCD
    """
    ERR_NORULES = "434"


    """

     This numeric can be found in:
    - IRCNet ircd
    """
    ERR_SERVICENAMEINUSE = "434"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    """
    ERR_BANNICKCHANGE_CHARYBDIS = "435"


    """

     This numeric can be found in:
    - Bahamut
    """
    ERR_BANONCHAN = "435"


    """

     This numeric can be found in:
    - IRCNet ircd
    - UnrealIRCD
    """
    ERR_SERVICECONFUSED = "435"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NICKCOLLISION = "436"


    """

     This numeric can be found in:
    - Bahamut
    - ircu
    - plexus
    - snircd
    - UnrealIRCD
    """
    ERR_BANNICKCHANGE = "437"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    - RFC2812
    """
    ERR_UNAVAILRESOURCE = "437"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_NCHANGETOOFAST = "438"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - snircd
    """
    ERR_NICKTOOFAST = "438"


    """

     This numeric can be found in:
    - Bahamut
    """
    ERR_TARGETTOFAST = "439"


    """

     This numeric can be found in:
    - ircu
    - plexus
    - snircd
    - UnrealIRCD
    """
    ERR_TARGETTOOFAST = "439"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircu
    - plexus
    - snircd
    - UnrealIRCD
    """
    ERR_SERVICESDOWN = "440"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_USERNOTINCHANNEL = "441"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NOTONCHANNEL = "442"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_USERONCHANNEL = "443"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    ERR_NOLOGIN = "444"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    ERR_SUMMONDISABLED = "445"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - UnrealIRCD
    """
    ERR_USERSDISABLED = "446"


    """

     This numeric can be found in:
    - Inspircd
    """
    ERR_CANTCHANGENICK = "447"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_NONICKCHANGE = "447"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NOTREGISTERED = "451"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_HOSTILENAME = "455"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    ERR_ACCEPTFULL = "456"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    ERR_ACCEPTEXIST = "457"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    ERR_ACCEPTNOT = "458"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_NOHIDING = "459"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_NOTFORHALFOPS = "460"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NEEDMOREPARAMS = "461"


    """

     This numeric can be found in:
    - Inspircd
    """
    ERR_ALREADYREGISTERED = "462"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_ALREADYREGISTRED = "462"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircu
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NOPERMFORHOST = "463"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_PASSWDMISMATCH = "464"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_YOUREBANNEDCREEP = "465"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircu
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_YOUWILLBEBANNED = "466"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircu
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_KEYSET = "467"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_INVALIDUSERNAME = "468"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - UnrealIRCD
    """
    ERR_ONLYSERVERSCANCHANGE = "468"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_LINKSET = "469"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - UnrealIRCD
    """
    ERR_LINKCHANNEL = "470"


    """

     This numeric can be found in:
    - ircd-hybrid
    """
    ERR_OPERONLYCHAN = "470"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_CHANNELISFULL = "471"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_UNKNOWNMODE = "472"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_INVITEONLYCHAN = "473"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_BANNEDFROMCHAN = "474"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_BADCHANNELKEY = "475"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircu
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_BADCHANMASK = "476"


    """

     This numeric can be found in:
    - plexus
    """
    ERR_OPERONLYCHAN_PLEXUS = "476"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - snircd
    - UnrealIRCD
    """
    ERR_NEEDREGGEDNICK = "477"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC2812
    """
    ERR_NOCHANMODES = "477"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_BANLISTFULL = "478"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - snircd
    """
    ERR_BADCHANNAME = "479"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_LINKFAIL = "479"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_CANNOTKNOCK = "480"


    """

     This numeric can be found in:
    - ircd-hybrid
    - ircd-ratbox
    """
    ERR_SSLONLYCHAN = "480"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    """
    ERR_THROTTLE = "480"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NOPRIVILEGES = "481"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_CHANOPRIVSNEEDED = "482"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_CANTKILLSERVER = "483"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_ATTACKDENY = "484"


    """

     This numeric can be found in:
    - Bahamut
    """
    ERR_DESYNC = "484"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircu
    - ircd-ratbox
    - snircd
    """
    ERR_ISCHANSERVICE = "484"


    """

     This numeric can be found in:
    - ircd-hybrid
    - IRCNet ircd
    - RFC2812
    """
    ERR_RESTRICTED = "484"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircd-ratbox
    """
    ERR_BANNEDNICK = "485"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - plexus
    """
    ERR_CHANBANREASON = "485"


    """

     This numeric can be found in:
    - snircd
    """
    ERR_ISREALSERVICE = "485"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_KILLDENY = "485"


    """

     This numeric can be found in:
    - RFC2812
    """
    ERR_UNIQOPPRIVSNEEDED = "485"


    """

     This numeric can be found in:
    - IRCNet ircd
    """
    ERR_UNIQOPRIVSNEEDED = "485"


    """

     This numeric can be found in:
    - snircd
    """
    ERR_ACCOUNTONLY = "486"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - UnrealIRCD
    """
    ERR_NONONREG = "486"


    """

     This numeric can be found in:
    - Bahamut
    """
    ERR_MSGSERVICES = "487"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_NOTFORUSERS = "487"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_HTMDISABLED = "488"


    """

     This numeric can be found in:
    - Bahamut
    """
    ERR_NOSSL = "488"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_SECUREONLYCHAN = "489"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircu
    - ircd-ratbox
    - snircd
    """
    ERR_VOICENEEDED = "489"


    """

     This numeric can be found in:
    - Inspircd
    """
    ERR_ALLMUSTSSL = "490"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_NOSWEAR = "490"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_NOOPERHOST = "491"


    """

     This numeric can be found in:
    - Inspircd
    - plexus
    - UnrealIRCD
    """
    ERR_NOCTCP = "492"


    """

     This numeric can be found in:
    - Inspircd
    """
    ERR_NOCTCPALLOWED = "492"


    """

     This numeric can be found in:
    - IRCNet ircd
    - RFC1459
    - RFC2812
    """
    ERR_NOSERVICEHOST = "492"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_NOFEATURE = "493"


    """

     This numeric can be found in:
    - Bahamut
    """
    ERR_NOSHAREDCHAN = "493"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_BADFEATVALUE = "494"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-seven
    """
    ERR_OWNMODE = "494"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_BADLOGTYPE = "495"


    """

     This numeric can be found in:
    - Inspircd
    """
    ERR_DELAYREJOIN = "495"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_BADLOGSYS = "496"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_BADLOGVALUE = "497"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_ISOPERLCHAN = "498"


    """

     This numeric can be found in:
    - plexus
    - UnrealIRCD
    """
    ERR_CHANOWNPRIVNEEDED = "499"


    """

     This numeric can be found in:
    - IRCNet ircd
    """
    ERR_STATSKLINE_RFC2812 = "499"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_TOOMANYJOINS = "500"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_UMODEUNKNOWNFLAG = "501"


    """

     This numeric can be found in:
    - Inspircd
    """
    ERR_UNKNOWNSNOMASK = "501"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - Inspircd
    - IRCNet ircd
    - ircd-seven
    - ircu
    - plexus
    - ircd-ratbox
    - RFC1459
    - RFC2812
    - snircd
    - UnrealIRCD
    """
    ERR_USERSDONTMATCH = "502"


    """

     This numeric can be found in:
    - Bahamut
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    ERR_GHOSTEDCLIENT = "503"


    """

     This numeric can be found in:
    - Bahamut
    """
    ERR_LAST_ERR_MSG_BAHAMUT = "504"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    ERR_USERNOTONSERV = "504"


    """

     This numeric can be found in:
    - Bahamut
    - ircu
    - snircd
    - UnrealIRCD
    """
    ERR_SILELISTFULL = "511"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_NOSUCHGLINE = "512"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - UnrealIRCD
    """
    ERR_TOOMANYWATCH = "512"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_BADPING = "513"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_NEEDPONG = "513"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    ERR_WRONGPONG = "513"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_NOSUCHJUPE = "514"


    """

     This numeric can be found in:
    - Bahamut
    - UnrealIRCD
    """
    ERR_TOOMANYDCC = "514"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_BADEXPIRE = "515"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_DONTCHEAT = "516"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircu
    - snircd
    - UnrealIRCD
    """
    ERR_DISABLED = "517"


    """

     This numeric can be found in:
    - ircd-hybrid
    - ircu
    - plexus
    - snircd
    """
    ERR_LONGMASK = "518"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_NOINVITE = "518"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_ADMONLY = "519"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_TOOMANYUSERS = "519"


    """

     This numeric can be found in:
    - Inspircd
    """
    ERR_CANTJOINOPERSONLY = "520"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_MASKTOOWIDE = "520"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_OPERONLY = "520"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - plexus
    - UnrealIRCD
    """
    ERR_LISTSYNTAX = "521"


    """

     This numeric can be found in:
    - Bahamut
    - UnrealIRCD
    """
    ERR_WHOSYNTAX = "522"


    """

     This numeric can be found in:
    - Bahamut
    - UnrealIRCD
    """
    ERR_WHOLIMEXCEED = "523"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    ERR_HELPNOTFOUND = "524"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_OPERSPVERIFY = "524"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_QUARANTINED = "524"


    """

     This numeric can be found in:
    - ircu
    """
    ERR_INVALIDKEY = "525"


    """

     This numeric can be found in:
    - snircd
    """
    ERR_BADHOSTMASK = "530"


    """

     This numeric can be found in:
    - Inspircd
    """
    ERR_CANTSENDTOUSER = "531"


    """

     This numeric can be found in:
    - snircd
    """
    ERR_HOSTUNAVAIL = "531"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_NOTLOWEROPLEVEL = "560"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_NOTMANAGER = "561"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_CHANSECURED = "562"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_UPASSSET = "563"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_UPASSNOTSET = "564"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_NOMANAGER = "566"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_UPASS_SAME_APASS = "567"


    """

     This numeric can be found in:
    - ircu
    - snircd
    """
    ERR_LASTERROR = "568"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_REAWAY = "597"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_GONEAWAY = "598"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_NOTAWAY = "599"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - UnrealIRCD
    """
    RPL_LOGON = "600"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - UnrealIRCD
    """
    RPL_LOGOFF = "601"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - UnrealIRCD
    """
    RPL_WATCHOFF = "602"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - UnrealIRCD
    """
    RPL_WATCHSTAT = "603"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - UnrealIRCD
    """
    RPL_NOWON = "604"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - UnrealIRCD
    """
    RPL_NOWOFF = "605"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - UnrealIRCD
    """
    RPL_WATCHLIST = "606"


    """

     This numeric can be found in:
    - Bahamut
    - ircd-hybrid
    - UnrealIRCD
    """
    RPL_ENDOFWATCHLIST = "607"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_CLEARWATCH = "608"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_NOWISAWAY = "609"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_MAPMORE_UNREAL = "610"


    """

     This numeric can be found in:
    - Bahamut
    - UnrealIRCD
    """
    RPL_DCCSTATUS = "617"


    """

     This numeric can be found in:
    - Bahamut
    - UnrealIRCD
    """
    RPL_DCCLIST = "618"


    """

     This numeric can be found in:
    - Bahamut
    - UnrealIRCD
    """
    RPL_ENDOFDCCLIST = "619"


    """

     This numeric can be found in:
    - Bahamut
    - UnrealIRCD
    """
    RPL_DCCINFO = "620"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_DUMPING = "640"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_DUMPRPL = "641"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_EODUMP = "642"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    RPL_SPAMCMDFWD = "659"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - UnrealIRCD
    """
    RPL_STARTTLS = "670"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircd-ratbox
    - UnrealIRCD
    """
    RPL_WHOISSECURE = "671"


    """

     This numeric can be found in:
    - plexus
    """
    RPL_WHOISSSL = "671"


    """

     This numeric can be found in:
    - plexus
    """
    RPL_WHOISCGI = "672"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - UnrealIRCD
    """
    ERR_STARTTLS = "691"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_COMMANDS = "702"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_MODLIST = "702"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_COMMANDSEND = "703"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_ENDOFMODLIST = "703"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_HELPSTART = "704"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_HELPTXT = "705"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_ENDOFHELP = "706"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircd-ratbox
    """
    ERR_TARGCHANGE = "707"


    """

     This numeric can be found in:
    - Charybdis
    - IRCNet ircd
    - ircd-seven
    - ircd-ratbox
    """
    RPL_ETRACEFULL = "708"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - ircd-ratbox
    """
    RPL_ETRACE = "709"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_KNOCK = "710"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_KNOCKDLVR = "711"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    ERR_TOOMANYKNOCK = "712"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    ERR_CHANOPEN = "713"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    ERR_KNOCKONCHAN = "714"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    ERR_KNOCKDISABLED = "715"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircd-ratbox
    """
    ERR_TARGUMODEG = "716"


    """

     This numeric can be found in:
    - ircd-hybrid
    - plexus
    """
    RPL_TARGUMODEG = "716"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_TARGNOTIFY = "717"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_UMODEGMSG = "718"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_OMOTDSTART = "720"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_OMOTD = "721"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_ENDOFOMOTD = "722"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    ERR_NOPRIVS = "723"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_TESTMASK = "724"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_TESTLINE = "725"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    RPL_NOTESTLINE = "726"


    """

     This numeric can be found in:
    - plexus
    """
    RPL_ISCAPTURED = "727"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircd-ratbox
    """
    RPL_TESTMASKGECOS = "727"


    """

     This numeric can be found in:
    - plexus
    """
    RPL_ISUNCAPTURED = "728"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    """
    RPL_QUIETLIST = "728"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    """
    RPL_ENDOFQUIETLIST = "729"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircd-ratbox
    """
    RPL_MONONLINE = "730"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircd-ratbox
    """
    RPL_MONOFFLINE = "731"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircd-ratbox
    """
    RPL_MONLIST = "732"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircd-ratbox
    """
    RPL_ENDOFMONLIST = "733"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircd-ratbox
    """
    ERR_MONLISTFULL = "734"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircd-ratbox
    """
    RPL_RSACHALLENGE2 = "740"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - ircd-ratbox
    """
    RPL_ENDOFRSACHALLENGE2 = "741"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - UnrealIRCD
    """
    ERR_MLOCKRESTRICTED = "742"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    """
    ERR_INVALIDBAN = "743"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    """
    ERR_TOPICLOCK = "744"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    """
    RPL_SCANMATCHED = "750"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    """
    RPL_SCANUMODES = "751"


    """

     This numeric can be found in:
    - IRCNet ircd
    """
    RPL_ETRACEEND = "759"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - UnrealIRCD
    """
    RPL_LOGGEDIN = "900"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - UnrealIRCD
    """
    RPL_LOGGEDOUT = "901"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - UnrealIRCD
    """
    ERR_NICKLOCKED = "902"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - UnrealIRCD
    """
    RPL_SASLSUCCESS = "903"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - UnrealIRCD
    """
    ERR_SASLFAIL = "904"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - UnrealIRCD
    """
    ERR_SASLTOOLONG = "905"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - UnrealIRCD
    """
    ERR_SASLABORTED = "906"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    - UnrealIRCD
    """
    ERR_SASLALREADY = "907"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-seven
    """
    RPL_SASLMECHS = "908"


    """

     This numeric can be found in:
    - Inspircd
    """
    ERR_WORDFILTERED = "936"


    """

     This numeric can be found in:
    - plexus
    - UnrealIRCD
    """
    ERR_CANNOTDOCOMMAND = "972"


    """

     This numeric can be found in:
    - Inspircd
    """
    ERR_CANTUNLOADMODULE = "972"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_UNLOADEDMODULE = "973"


    """

     This numeric can be found in:
    - plexus
    - UnrealIRCD
    """
    ERR_CANNOTCHANGECHANMODE = "974"


    """

     This numeric can be found in:
    - Inspircd
    """
    ERR_CANTLOADMODULE = "974"


    """

     This numeric can be found in:
    - Inspircd
    """
    RPL_LOADEDMODULE = "975"


    """

     This numeric can be found in:
    - Charybdis
    - ircd-hybrid
    - ircd-seven
    - plexus
    - ircd-ratbox
    """
    ERR_LAST_ERR_MSG = "999"


    """

     This numeric can be found in:
    - UnrealIRCD
    """
    ERR_NUMERICERR = "999"


    """

     This numeric can be found in:
    - Bahamut
    """
    ERR_NUMERIC_ERR = "999"
