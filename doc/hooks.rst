Signals
=====

Signals are the heart of PyIRC and are how events are dispatched. Signals are
implemented with taillight_, a library for signals and slots, that implements
priorities, event suspension and resumption, and more.

.. _taillight: http://github.com/Elizafox/taillight

.. warning::
   TODO: add examples on @event decorator and stuff.

.. toctree::
   :maxdepth: 2

Event classes
-------------

Signal names are separated into classes and events. The classes are a form of
virtual namespace. All events in the same class should accept the same
parameters. When a signal is called, it will always receive a
:py:class:`~PyIRC.base.Event` class, which can be used to share data between
the events. Other args passed in depend on the event. The PyIRC convention is
presently that the ``Event`` instance is passed in as ``caller``, though this
is subject to change (as it is simply convention and not required by anything
in particular).

cap_perform
^^^^^^^^^^^

Arguments: ``caller, caps``

``caps`` are a set of caps being dealt with by the event.

Use this to event when to execute CAPs during either a CAP ACK or a CAP NEW
event.

commands
^^^^^^^^

Arguments: ``caller, line``

``line`` is the :py:class:`~PyIRC.line.Line` triggering this command.

IRC commands are handled by this. The event called is the command to process.
This is similar to how most clients and servers process commands.

The event can either be a :py:class:`~PyIRC.numerics.Numeric` enum member, or a
string representing the command.

commands_cap
^^^^^^^^^^^^

Arguments: ``caller, line``.

``line`` is the :py:class:`~PyIRC.line.Line` triggering this command.

This is used to handle CAP subcommands (as specified by the event) in a more
scrutable way. The most interesting thing to most clients is the ``ack``
subcommand, used to acknowedge capabilities.

.. note::
   These events requires the :py:class:`~PyIRC.extensions.cap.CapNegotiate`
   extension.

commands_ctcp
^^^^^^^^^^^^^

Arguments: ``caller, ctcp, line``

``ctcp`` is the :py:class:`~PyIRC.auxparse.CTCPMessage` received.

``line`` is the :py:class:`~PyIRC.line.Line` received.


These events is used by the :py:class:`~PyIRC.extensions.CTCP` extension to
call CTCP events. VERSION and PING events are implemented by default.

A :py:class:`~PyIRC.extensions.ctcp.CTCPEvent` is passed in, which passes in
the :py:class:`~PyIRC.auxparse.CTCPMessage` from the event.

.. note::
   These events requires the :py:class:`~PyIRC.extensions.CTCP` extension.

commands_nctcp
^^^^^^^^^^^^^^

Arguments: ``caller, ctcp, line``

``ctcp`` is the :py:class:`~PyIRC.auxparse.CTCPMessage` received.

``line`` is the :py:class:`~PyIRC.line.Line` received.

These events is used by the :py:class:`~PyIRC.extensions.CTCP` extension to
call NCTCP events; that is, the reply to CTCP queries. No events are
registered by default.

.. note::
   These events requires the :py:class:`PyIRC.extensions.CTCP` extension.

protocol
^^^^^^^^

Arguments: ``caller``

The class for protocol events, such as the casemapping being changed (which
happens on connection).

link
^^^^

Arguments: ``caller``


The class for link events (connection and disconnection).

modes
^^^^^

Arguments: ``caller, setter, target, mode``

``setter`` is the :py:class:`~PyIRC.line.Hostmask` of the mode setter, if
known.

``target`` is the channel (or more rarely, nick) the mode is being applied to.

``mode`` is the :py:class:`~PyIRC.extensions.basetrack.Mode` being passed in.

These events emit easier-to-use events for modes, as opposed to parsing
``MODE`` commands yourself.

.. note::
   These events requires the :py:class:`~PyIRC.extensions.basetrack.BaseTrack`
   extension.

scope
^^^^^

Arguments: ``caller, scope``

``scope`` is a :py:class:`~PyIRC.extensions.basetrack.Scope` instance.

These events emit events when a user either becomes visible (connects/joins),
or loses visibility (leaves/disconnects).

.. note::
   These events require the :py:class:`~PyIRC.extensions.basetrack.BaseTrack`
   extension.

More specific events
--------------------

The most important default events called by PyIRC are documented here. Of
course, it is not possible to document every last event (not to mention event
classes are open-ended on purpose).

cap_perform
^^^^^^^^^^^

ack
"""

Use this to do the initial handshake. To keep other caps from running, cancel
the event. Processing can be resumed using
:py:meth:`~PyIRC.extensions.cap.CapNegotiate.cont`.

commands_cap
^^^^^^^^^^^^

Whilst it is not necessarily useful to event all of the CAP subcommands, the
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

protocol
^^^^^^^^

case_change
"""""""""""
The event called when the casemapping changes on the server.  Normally only
called once, when RPL_ISUPPORT (numeric 005) is received, but may be called at
any time.

link
^^^^

connected
"""""""""

The event called when we establish a connection to the server, and are
starting the handshake.

disconnected
""""""""""""

The event called when the connection is lost to the server. Use this event to
reset any state in your extension to a known state, in case of a reconnection
attempt.

modes
^^^^^

These events are fired upon mode change.

mode_prefix
"""""""""""

Fired when a mode that alters a user's status in channel (anything in PREFIX)
is received by us. This is also fired for NAMES prefixes upon initial join.

.. note::
   In the future, this may be fired for WHOIS channel enumeration.

mode_list
"""""""""

Fired when receiving a list mode (the first group in CHANMODES in ISUPPORT).
This includes bans, invite exceptions, ban exceptions, and the like.

mode_key
""""""""

Fired when receiving a mode that takes a parameter for setting but not
unsetting. The sole member of this class is usually ``+k``, hence the name.

mode_param
""""""""""

Fired when receiving a mode that takes a parameter for both setting and
receiving. Most modes taking parameters fall into this category, such as
``+f``, ``+j``, etc.

mode_normal
"""""""""""

Fired when receiving a mode that takes no parameters. This is the vast
majority of modes, and includes ``+c``, ``+t``, etc.

scope
^^^^^

These events are fired when a user enters or leaves scope.

user_join
"""""""""

Fired when a user joins a channel.

user_burst
""""""""""

Fired when multiple users join a channel, one event per user.

user_part
"""""""""

Fired when a user leaves a channel.

user_kick
"""""""""

Fired when a user is removed from a channel by an administrator.

user_quit
"""""""""

Fired when a user disconnects from IRC.
