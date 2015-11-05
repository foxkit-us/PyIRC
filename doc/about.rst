About
=====

.. toctree::
   :maxdepth: 2

PyIRC is an IRC library designed for everything from ancient IRC 2.8 servers
to modern IRCv3 compliant servers, and everything in between. It is designed
to be modular, flexible, and easy to use.

Why should I use PyIRC?
-----------------------

Despite the initial appearance, PyIRC is nothing more than a way to turn IRC
commands into callbacks and accessible data, whilst optionally doing the
legwork of handling the boring parts of IRC. No, really, that's it. It doesn't
try to take over your event loop, it doesn't try to dominate your application,
it doesn't believe it is the centre of the universe. It simply just eats IRC
events and does actions/state keeping based on them. How you put in the events
is up to you, but we do provide several network layers.

To facilitate this goal, PyIRC is designed to allow use of modern features
where you require or want them, and yet allow for features to be foregone when
desired or necessary. It also aims for correctness with most modern IRC
servers; a lot of libraries are known to be incorrect in the implementation of
many features, particularly in IRC message parsing.

Everything in the library revolves around the concept that nothing is an
absolute hard requirement, and that things can be reimplemented with ease by
advanced users. At the same time, functionality for those who don't want to
mess with the internals of the protocol is there and as functional as possible
within reason.

PyIRC is also designed to have minimal dependencies. Requirements ought not to
be hoisted upon a user when possible. The only requirement is a Python 3.3
interpreter and above, and 3.2 support could be done with minimal work. That's
all.

No attempt is made to support Python 2.x as that series is so broken with
Unicode that it's not worth our time. This is our sole exception to the above.
Guido says they'll support Python 2.7 until 2020; that doesn't mean we have
to.

Architecture
------------

To hide the complexities of modern IRC as well as possible, whilst supporting
legacy servers, we have designed the system (after much careful thought) to be
extensible, flexible, and at the same time, unobtrusive. We try to stay out of
your way where practical, but provide useful things to the user behind the 
scenes, with little to no intervention on their part.

Whilst internally PyIRC may seem very complex at first shake, it actually has
a rather simple design, with the goal for it to be simple to use by anyone,
from the newbie to IRC who just wants a working bot, to the advanced user who
may be writing a bot for IRC operator functions and tasks.

A not-so-brief word about modern IRC
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before continuing, it's necessary to get a picture of how truly complicated
modern IRC is, and why PyIRC is designed the way it is (arguably increasing
complexity).

Many members of our team have worked previously on various IRC daemons, and
have even participated in the `IRCv3 workgroup`_. We are acutely aware of the
very real issues faced by IRC libraries that exist in Python today, and their
ad-hoc support for many IRC features, especially because no one central
authority has done more than a token effort to document IRC as actually used
on modern servers (those who have often have political agendas and their own
novel standards injected, some of which have never seen widespread use).

The reason that IRC is in such a sorry state in terms of documentation is due
the fact that the protocol actually used by IRC servers does not reflect
RFC1459_ anymore, and has not for many years. Many numerics are obsolete,
superseded, or not even listed in the standard. There are also numerous
undocumented commands. Contrast that to RFC2812_, the "updated" version of
RFC1459, which is best interpreted as something akin to any ancient accounts
of the history of Rome - a bizarre blend of fact and fiction, but where fact
ends and fiction begins (or vice versa) is impossible to tell. Even the
authors of the standard, IRCNet, break it in several ways.

Despite this, many standards such as CTCP_, DCC_, ISUPPORT_, WHOX_, NAMESX_,
PROTOCTL_, CAP_, and countless others have cropped up, with various degrees of
documentation. However, to rub salt into the already open, festering wounds,
many of these new specifications themselves have become out of date. For
example:

- Nobody implements the CTCP quoting specification in full, and nor have they
  ever; it is completely abominable, a bad solution to a non-problem, and can
  lead to flooding if ever actually implemented according to specification
- mIRC formatting codes - oh my goodness... nobody can agree on the shades of
  the colours, there's only 16 in most clients (1989 called, they want their
  graphics cards back), and then you have the essentially "non-standard"
  italic and strikethrough extensions implemented in hundreds of different
  ways... then the blinking text specifiers, largely an accident due to bad
  filtering in terminals... \*shudder\*...
- DCC has dozens of extensions with spotty implementation; little more than
  SEND, RECV, and CHAT can be safely used, and possibly passive support.
- ISUPPORT has sprouted many different ways to advertise the same features,
  often in the same IRC software, and the lowest common denominator is what
  mIRC understands
- STATS itself is a disaster. Every IRC daemon uses their own format strings,
  their own numerics, and few are compatible.
- LIST is not safe on many IRC servers; it can fill the client's send queue
  and knock them off the network. Some servers have SAFELIST, which throttles
  the query.
- The other "list" modes (AKA "bantypes") besides +b. +e for excepts. +I for
  invites. +q for quiets (except on some IRC daemons where that means owner).
- "Enhanced" prefixes like owner, admin, and halfop. What do they even mean?
  What can they even do? Depends on which IRC daemon you ask.
- Aside from SASL, the bolted-on second-class state of services - much blood
  has been spilled trying to get services authors to agree even on the
  simplest of points because of political reasons.
- PROTOCTL, a sort of primitive and poorly-documented feature negotiation,
  duplicates CAP (although CAP came later, and is far less primitive). Namely,
  it duplicates CAP userhost-in-names and multi-prefix (with NAMESX and
  UHNAMES).

With the proliferation of these additional sub-standards (often themselves
substandard ;) comes the problem of incompatibility. Oftentimes, this
incompatibility is subtle. For example, for maximum security (especially with
STARTTLS and SASL in combination), IRC daemons should issue CAP before
"registration" with the server (that is, presenting their username, GECOS, and
nick). However, if CAP is unavailable, a server will simply never respond to
the command. This mandates a timeout being required for CAP, to ensure that
compatibility with older servers is maintained. This timeout, of course,
introduces latency.

Naturally of course, many clients do not need all these features presented by
modern IRC. This leads to the unfortunate side effect that most IRC libraries
are excessively simple.

Although the `IRCv3 workgroup`_ is attempting to fix this with a full-fledged
standards effort (with an RFC in the works), legacy servers and those who do
not follow the new standard (for political or "not-invented-here" reasons)
are an unfortunate reality. Pressure will hopefully reduce or eliminate these
pretenders to the IRC standards throne, but for the time being, these servers
exist today, and the standards effort is far from complete.

In the meantime, it is certainly desirable that clients should be able to take
full advantage of these features, without having to worry about the involved
complexity of implementing them. It is also desirable that users who do not
need these features do not have to be forced to use them. This has influenced
the architecture of PyIRC greatly.

Concepts
^^^^^^^^

PyIRC's four main architectural concepts are:

- Extensions, providing an easy way to stack and mix/match features
- Hooks, providing a way to run events implemented by the extensions, and
  ensure the callback chain is executed correctly
- The base class, which brings together extensions and hooks to process the
  protocol
- The io class, which inherits from the base class and implements the final
  pieces of the puzzle

Extensions
^^^^^^^^^^

PyIRC uses extensions to allow its functionality to be tweaked per-network and
per-application as needed. By using extensions, end-users can tweak the
desired functionality of the library, without having to worry about ordering
or conflicts, whilst omitting things they don't need or don't want.

Extensions are passed in to the base IRC class as a list of uninstantiated
classes, which are then built into an extensions database for later lookup
and retrieval.

Extensions all inherit from the :py:class:`~PyIRC.extension.BaseExtension`
class, which redirects all methods not known about it to the base class (to
ensure extensions and the base look the same if code is copied between the two).

Extensions can set requirements; the requirements list can either use strings,
or other :py:class:`~PyIRC.extension.BaseExtension` instances. If they are
strings, then they are looked up by known ``BaseExtension`` subclasses first
(and all their derivative subclasses). If none are found, an attempt is made
to look up a builtin extension. If this fails, the library punts.

.. note::
  All extensions are optional by design, and you are free to implement your
  own.

Signals
^^^^^^^

IRC is a very stateful protocol, with a myriad of non-standard extensions that
require a very complex chain of events to be implemented in an exacting order.
For example, STARTTLS must be executed after the capability is reported by the
server, but before we tell the server our username, nickname, and password (to
avoid information leaks). However, the CAP extension needed for this may not be
available at all!

To facilitate this mess, PyIRC uses the concept of signals and slots as
implemented by taillight_. The signals are fired as ``(hookclass, event)``,
and are unique per connection. The hook class describes the broad class of
event that is occurring (command, commands_ctcp, etc). It is a sort of
virtual namespace for the event that is being fired, to avoid conflicts.

Naturally, these signals can be called, suspended, and resumed. This is used
to implement the complex state machine required for modern IRC. The semantics
for this are essentially those as used in taillight, except for one exception:
always call :py:meth:`~PyIRC.base.IRCBase.call_event` and
:py:meth:`~PyIRC.base.IRCBase.call_resume`, since asyncio and normal sockets
differ in how these are implemented (don't worry, the I/O system handles the
difference for you).

Individual slots and even entire signals, of course, can be removed. See also
:py:class:`~PyIRC.signal.SignalBase` and its methods.

Base
^^^^

The base class contains the glue for extensions and hooks, bringing them
together into a cohesive unit. The base class also contains some minimal state
that extensions can rely on.

IRC data is injected via the recv method, and lines are sent out via the send
method. In the recv method, the data is parsed, and the correct commands hook
is run.

The base class also contains functions for scheduling events in the future.
Many things in IRC require timeouts or throttling; this is used to implement
such a model. How scheduling is implemented is up to the given io backend.

In the future, the role of base may be expanded as sort of a data registry for
extensions, to allow reloading and runtime removal of extensions.

io
^^

The io system subclasses Base to add the final piece of the puzzle - shoving
data into the library. It implements the actual sending and recieving of data
from the network. It also implements scheduling. There is at present an
asyncio and socket backend. A gevent backend may be created in the future.

Using PyIRC
-----------

PyIRC is pretty simple to use:

.. code:: python

    from PyIRC.io.socket import IRCSocket
    from PyIRC.extensions import bot_recommended

    arguments = {
        'serverport' : ('irc.interlinked.me', 9999),
        'ssl' : True,
        'username' : 'Testbot',
        'nick' : 'Testbot',
        'gecos' : 'I am a test, pls ignore :)',
        'extensions' : bot_recommended,
        'sasl_username' : 'Testbot',
        'sasl_password' : 'loldongs123',
        'join' : ['#PyIRC'],
    }

    i = IRCSocket(**arguments)
    i.loop()

Yes, it's that easy. No fuss, no muss.

.. _CAP: http://ircv3.net/specs/core/capability-negotiation-3.1.html

.. _CTCP: http://www.irchelp.org/irchelp/rfc/ctcpspec.html

.. _DCC: http://www.irchelp.org/irchelp/rfc/dccspec.html

.. _`IRCv3 workgroup`: http://ircv3.net/

.. _ISUPPORT: http://www.irc.org/tech_docs/005.html

.. _NAMESX: https://bugs.unrealircd.org/view.php?id=2833

.. _RFC1459: https://tools.ietf.org/html/rfc1459

.. _RFC2812: https://tools.ietf.org/html/rfc2812

.. _PROTOCTL: https://www.unrealircd.org/files/docs/technical/protoctl.txt

.. _UHNAMES: http://ircv3.net/specs/extensions/userhost-in-names-3.2.html

.. _WHOX: http://faerion.sourceforge.net/doc/irc/whox.var

.. _taillight: http://github.com/Elizafox/taillight
