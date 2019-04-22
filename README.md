# PyIRC
This is PyIRC, an IRC library designed to be flexible, extensible, well-
documented, and easy to use. It is aimed at not only beginners and those who
don't want to spend too much time writing boilerplate to get something going¸
but also the advanced user who knows exactly what they're doing.

It is entirely written in Python 3 with only optional external dependencies.

## Introduction
Written by people who have been involved in IRC daemon coding for over 7
years, this library has been designed with standards compliance in mind. This
library aims to follow [RFC1459](http://tools.ietf.org/html/rfc1459.html),
[RFC2812](http://tools.ietf.org/html/rfc2812.html), and
[IRCv3](http://ircv3.org)

The following standards should be fully implemented:
* RFC1459 (though not all commands are handled because they are beyond the
  scope of the library)
* RFC2812 (the different USER syntax is not well-supported, and is not used)
* IRCv3.0
* IRCv3.1

The following standards are not fully implemented:
* IRCv3.2 (tags and some capabilities should work, but most capabilities are
  not presently implemented; there are also few implementations right now).

The library presently supports the following using an extensions system,
meaning all of these are optional:
- Channel autojoin
- Autorejoin on kick
- STARTTLS (automatic SSL negotiation)
- IRCv3 Message tags, though not thoroughly tested
- SASL (PLAIN auth only right now - more methods are coming)
- CAP - dynamic capabilities negotiation
- Scheduled events (aka timers)
- Ability to hook any numeric/command
- Ability to hook connect, disconnect, and a variety of other higher-level
  events

See the [TODO](https://code.foxkit.us/IRC/PyIRC/blob/master/TODO.md) for the
list of planned features.

## Design
PyIRC 3 is designed to be wholly uncoupled from the underlying I/O subsystem
whilst providing easy ways to ingest events. It is designed to work with any
reasonably well-written event system.

This library is not thread-safe and therefore caution should be used when
using PyIRC with threads. It does not, however, modify state outside of its
own classes, so it's safe to run instances in threads.

## Platforms
The library is completely cross-platform and should work anywhere Python does,
so long as it has a working socket implementation (SSL usage depends on your
Python build having support for the `ssl` module - this should be almost all
modern platforms).

PyIRC 3 requires Python 3.3 or newer. asyncio support requires either 3.4, or
for asyncio to be installed from PyPI.

## Documentation
Documentation is automatically generated and placed
[here](http://foxkit.us/PyIRC/) for perusal. Our docs coverage is very
complete.

## Bugs
Probably many! Tell us about them - see the support section or just file an
issue on the [bug tracker :)](https://code.foxkit.us/IRC/PyIRC/issues).

## Support
We can be reached easily at irc.interlinked.me #PyIRC for general questions.
Pull requests and patches are always welcomed. Features can be requested via
the bug tracker.

## License and copyright
Copyright © 2013-2015 A. Wilcox and Elizabeth Myers. All rights reserved.
Copyright © 2019 A. Wilcox.  All rights reserved.

Non-third party files are licensed under the WTFPL; terms and conditions can be
found at:

	http://www.wtfpl.net/about/

Selon votre choix, vous pouvez aussi utiliser la Licence Publique Rien À
Branler (LPRAB):

	http://sam.zoy.org/lprab/

