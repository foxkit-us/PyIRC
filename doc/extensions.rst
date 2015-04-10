Extensions
==========

.. toctree::
   :maxdepth: 2

This chapter presents the extensions that are included by default with PyIRC.

autojoin - Join channels on connection
--------------------------------------

.. autoclass:: PyIRC.extensions.autojoin.AutoJoin
   :special-members:
   :members:

basicrfc - Bare minimum IRC RFC standards support
----------------------------------------------------------------

.. autoclass:: PyIRC.extensions.basicrfc.BasicRFC
   :special-members:
   :members:

cap - Base IRCv3 CAP negotiation
--------------------------------

.. autoclass:: PyIRC.extensions.cap.CapNegotiate
   :special-members:
   :members:

channeltrack - Track channels that we have joined and their associated data
----------------------------------------------------------------------------

.. autoclass:: PyIRC.extensions.channeltrack.ChannelTrack
   :special-members:
   :members:

ctcp - Better CTCP message handling
-----------------------------------

.. autoclass:: PyIRC.extensions.ctcp.CTCP
   :special-members:
   :members:

.. autoclass:: PyIRC.extensions.ctcp.CTCPEvent
   :members:

isupport - the ISUPPORT extension
---------------------------------

.. autoclass:: PyIRC.extensions.isupport.ISupport
   :special-members:
   :members:

lag - get the current latency to the server
-------------------------------------------

.. autoclass:: PyIRC.extensions.lag.LagCheck
   :special-members:
   :members:

sasl - authenticate to services using SASL
------------------------------------------

.. autoclass:: PyIRC.extensions.sasl.SASLBase
   :special-members:
   :members:

.. autoclass:: PyIRC.extensions.sasl.SASLPlain
   :special-members:
   :members:

services - utilities for interacting with IRC services
------------------------------------------------------

.. autoclass:: PyIRC.extensions.services.ServicesLogin
   :special-members:
   :members:

