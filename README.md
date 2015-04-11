PyIRC
-----
This is PyIRC, an IRC library designed to be flexible, extensible, usable, and
useful. It is entirely written in Python with no required external
dependencies.

This is a rewrite of a rewrite, so you may see PyIRC 3 sprinkled in some
comments. Much has been learned from the first two efforts (PyIRC 1 had many
issues with being too monolithic, and had too many Unicode problems due to
Python 2 compatibility. PyIRC 2 was a bad API design (using subclassing) that
never could be properly rewritten). Some of the code has been retained from
PyIRC 2, where appropriate.

See LICENSE for details on distribution of this README and the software itself.

Introduction
============
This library has been designed with standards compliance in mind and as a goal.
Relevant standards include [RFC1459](http://tools.ietf.org/html/rfc1459.html),
[RFC2812](http://tools.ietf.org/html/rfc2812.html), and
[IRCv3](http://ircv3.org). RFC1459 and RFC2812 compliance is basically finished
(the different USER syntax in RFC2812 is not well-supported), as well as IRCv3.0
support. IRCv3.1 support should be fairly complete - if you notice any gaps,
please file a bug. Features of IRCv3.2 are mostly done, but may not be tested,
due to the lack of servers implementations.

The library presently supports the following in extensions:
- Autojoin
- STARTTLS
- Message tags (some parsing is attempted, but largely untested yet)
- SASL, PLAIN auth only right now
- CAP 
- Scheduled events
- Ability to hook any numeric/command and many events

See the [TODO](http://github.com/Elizafox/PyIRC/blob/master/TODO.md) for the
list of planned features.

Design
======
PyIRC 3 is designed to be wholly uncoupled from the underlying I/O subsystem
whilst providing easy ways to ingest events. It is designed to work around
your event system, not the other way around.

Please note the library is not thread-safe at this time, although some locking
is implemented (mostly sendq related stuff). If such functionality is desired,
it will be added.

Platforms
=========
The library is completely cross-platform and should work anywhere Python does,
so long as it has a working socket implementation (SSL usage depends on your
Python build having support for the `ssl` module - this should be almost all
modern platforms).

PyIRC 3 requires Python 3.3 or newer. asyncio support requires either 3.4, or
for asyncio to be installed from PyPI.

Bugs
====
Probably many! Tell us about them - see the support section or just file an
issue on the [bug tracker :)](http://github.com/Elizacat/PyIRC/issues).

Support
=======
Point your IRC client irc.interlinked.me #PyIRC for general questions, or file
an issue/pull request on github. Feature requests are also accepted this way.

License and copyright
=====================
Copyright © 2013-2015 Andrew Wilcox and Elizabeth Myers. All rights reserved.

Non-third party files are licensed under the WTFPL; terms and conditions can be
found at:

	http://www.wtfpl.net/about/

Selon votre choix, vous pouvez aussi utiliser la Licence Publique Rien À
Branler (LPRAB):

	http://sam.zoy.org/lprab/

