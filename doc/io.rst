IO backends
===========

This module contains the I/O backends for PyIRC. The backends inherit from
``IRCBase`` to pump messages in and out of the library, and perform scheduling
functions.

.. toctree::
   :maxdepth: 2

asyncio
-------

.. automodule:: PyIRC.io.asyncio
   :members:

socket
------

.. automodule:: PyIRC.io.socket
   :members:

