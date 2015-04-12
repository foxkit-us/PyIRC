Hooks
=====

Hooks are used in PyIRC to trigger various events to occur. Callbacks can be
registered and deregistered at will. See the ``EventManager`` class for more
details on how to do that.

.. warning::
   TODO: add examples on @hook decorator and stuff.

.. toctree::
   :maxdepth: 2

Event classes
-------------

Hooks are broadly separated into classes. Event classes act as a form of
namespace, where individual event types live. All events in the same class
use the same ``Event`` subclass, which is instantiated and passed in to the
events on event call, also passing in any data required.

This section documents the event classes and hooks used by PyIRC and its
extensions. Extensions can add their own event classes via the hook_classes
attribute. Conflicts are simply ignored (last one to register in the
extensions list wins).

commands
^^^^^^^^

IRC commands are handled by this. The event called is the command to process.
This is similar to how most clients and servers process commands.

The event can either be an IRC numeric or a string representing the command.

A ``LineEvent`` is passed to each callback, containing the line that triggered
the event.

commands_cap
^^^^^^^^^^^^

.. note::
   This hook requires the ``CapNegotiate`` extension.

CAP subcommands are handled using this event. The most interesting thing to
most clients is the ``ack`` subcommand, used to acknowedge capabilities.
However, any subcommand may be hooked.

hooks
^^^^^

.. warning::
   This will be renamed/broken up at some point in the future.

The catch-all for many default events, particularly connection events.

A ``HookEvent`` is passed in.

commands_ctcp
^^^^^^^^^^^^^

.. note::
   This hook requires the ``CTCP`` extension.

This hook is used by the ``CTCP`` extension to call CTCP events. VERSION and
PING events are implemented by default.

A ``CTCPEvent`` is passed in, which passes in the ``CTCPMessage`` from the
event.

commands_nctcp
^^^^^^^^^^^^^^

.. note::
   This hook requires the ``CTCP`` extension.

This hook is used by the ``CTCP`` extension to call NCTCP events; that is, the
reply to CTCP queries. No events are registered by default.

A ``CTCPEvent`` is passed in, which passes in the ``CTCPMessage`` from the
event.

Events
------

The most important default events called by PyIRC are documented here. Of
course, it is not possible to document every last hook (not to mention hook
classes are open-ended on purpose).

commands_cap
^^^^^^^^^^^^

Whilst it is not necessarily useful to hook all of the CAP subcommands, the
ones you likely want are documented here.

ack
"""

The ``ack`` event is used to acknowledge capabilities and do necessary
processes before the handhshake completes. In this way, it acts as a sort of
"pipeline" of events, that can be stalled in a specific order to achieve an
orderly handshake. To stall the ``ack`` "pipeline", set the ``LineEvent``
status member to cancelled, and do your part of the handshake. Be prepared to
handle errors, and to abort your stage of the handshake if needed and resume
processing, or even to abort the connection if the error is that fatal. When
you are finished with your portion of the handshake, call the
``CapNegotiate.cont`` callback to continue the handshake. This calls the
``ack`` hook again, so ensure you keep a flag to ensure you don't end up in an
infinite loop. Deregistering the event is also an option.

.. warning::
   Remember to reset all flags and events on close!

hooks
^^^^^

connected
"""""""""

The event called when we establish a connection to the server, and are
starting the handshake.

disconnected
""""""""""""

The event called when the connection is lost to the server. Use this event to
reset any state in your extension to a known state, in case of a reconnection
attempt.


