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

cap_perform
^^^^^^^^^^^

Use this to hook when to execute CAPs during either a CAP ACK or a CAP NEW
event.

A ``CAPEvent`` is passed in.

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

cap_perform
^^^^^^^^^^^

ack
"""

Use this to do the initial handshake. To keep other caps from running, cancel
the event. Processing can be resumed using ``CapNegotiate.cont()``.

commands_cap
^^^^^^^^^^^^

Whilst it is not necessarily useful to hook all of the CAP subcommands, the
ones you likely want are documented here.

end
"""

Can be used to ensure that, if you are expecting new caps to arrive, that your
callbacks won't be confused when called again later after the handshake ends.

ls
""

Use this to dynamically allow for injection of caps, although it's recommended
you simply make your ``caps`` variable a property instead, dynamically
controlled by current state.

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


