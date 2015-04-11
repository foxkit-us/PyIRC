# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


""" Rejoin automatically after being kicked from a channel.

This extension is also meant to serve as an example for extension authors.  It
is heavily documented and designed to be very easy to follow.
"""


# We use the standard partial method from functools for our scheduled callback.
from functools import partial
# PyIRC uses the standard Python logging framework.
from logging import getLogger

# * All extensions inherit from BaseExtension.
# * hook is the decorator for event handlers.
# * PRIORITY_LAST is a helpful constant for extensions that don't need immediate
#   procesing/filtering of messages.
from PyIRC.extension import BaseExtension
from PyIRC.hook import hook, PRIORITY_LAST


# Initialise our logger.
logger = getLogger(__name__)


class KickRejoin(BaseExtension):
    """ Rejoin a channel automatically after being kicked or removed. """

    requires = ["BasicRFC"]
    """ Describes what extensions are required to use this extension.  We use
    the :py:class:`basicrfc.BasicRFC` extension for nick tracking. """

    def __init__(self, base, **kwargs):
        """ Initialise the KickRejoin extension.

        Keyword arguments:

        rejoin_delay
            Seconds to delay until the channel is rejoined.  This defaults to 5,
            but can be set to anything.  Some people may think you're rude if
            you set it to 0.
        rejoin_on_remove
            Boolean defining whether to rejoin if you are 'removed'.  Note that
            most servers propogate REMOVE as KICK to clients so it won't always
            work (the sole exception in testing this extension was Freenode).
            Defaults to True, because REMOVE is silly anyway.
        """

        # Allow us to access the base class later on.  This is common to every
        # extension.
        self.base = base

        # Read our configuration variables from kwargs.  You should always have
        # sane defaults.
        self.rejoin_delay = kwargs.pop('rejoin_delay', 5)
        self.rejoin_on_remove = kwargs.pop('rejoin_on_remove', True)

        # Keep a calendar, this way you will always know what rejoins are going
        # to fire.  (This is used to cancel all pending rejoins if we are
        # disconnected.)
        self.scheduled = {}

    @hook("commands", "KICK")
    @hook("commands", "REMOVE")
    def on_kick(self, event):
        """ Command handler for KICK and REMOVE.

        This method receives a LineEvent object as its parameter, and will use
        it to determine if we were the ones kick/removed, and what action to
        take.
        """

        # Retrieve the BasicRFC extension handle.
        basicrfc = self.get_extension("BasicRFC")

        # Determine if the kicked user is us.
        if event.line.params[1] != basicrfc.nick:
            return  # It isn't us, so we don't care.

        # If this was a REMOVE and the user is being 'nice', ignore.
        if event.line.command == 'REMOVE' and not self.rejoin_on_remove:
            return

        # What channel were we kicked from?
        channel = event.line.params[0]

        # If we already pending rejoin, don't bother.
        # (XXX is this even possible?)
        if channel in self.scheduled:
            return

        # Schedule the join for `rejoin_delay` seconds from now.
        future = self.schedule(self.rejoin_delay, partial(self.join, channel))
        # and add it to the list of scheduled rejoins.
        self.scheduled[channel] = future

    def join(self, channel):
        """ Join the specified channel and remove the channel from the pending
        rejoin list. """

        self.send("JOIN", [channel])
        del self.scheduled[channel]

    @hook("hooks", "disconnected")
    def on_disconnected(self, event):
        """ Disconnection event handler.

        We must ensure that any pending rejoins are unscheduled, so that we
        don't do something silly like sending JOIN to a closed socket.
        """

        for future in self.scheduled.values():
            try:
                self.unschedule(future)
            except ValueError:
                pass  # XXX why?

        self.scheduled.clear()

# That's it!
# Pretty nifty, huh?  53 lines (not including documentation) to automatically
# rejoin channels when kicked or removed.  Now try it out!
