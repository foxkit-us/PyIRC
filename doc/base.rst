Base library
============

.. toctree::
   :maxdepth: 2

Events
------
PyIRC is built on a powerful yet easy-to-use event system.  In addition to
command events (each command and numeric has its own event you can hook), your
code can define its own event types wherever necessary - for example, the CTCP
extension defines a CTCP message event.

Event callbacks are registered using a decorator, @hook.  A single method can be
registered for multiple callbacks, however each event can only have one callback
per class at this time.

EventManager
^^^^^^^^^^^^

.. autoclass:: PyIRC.event.EventManager
   :members:

Event
^^^^^

.. autoclass:: PyIRC.event.Event
   :members:

EventState
^^^^^^^^^^

.. autoclass:: PyIRC.event.EventState
   :members:
