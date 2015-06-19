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

    requires = ["BasicRFC", "ISupport"]
    """ Describes what extensions are required to use this extension.  We use
    the :py:class:`basicrfc.BasicRFC` extension for nick tracking.
    :py:class:`isupport.ISupport` is used for prefixes discovery.
    """

    def __init__(self, *args, **kwargs):
        """ Initialise the KickRejoin extension.

        :key rejoin_delay:
            Seconds to delay until the channel is rejoined.  This defaults to 5,
            but can be set to anything.  Some people may think you're rude if
            you set it to 0.
        :key rejoin_on_remove:
            Boolean defining whether to rejoin if you are 'removed'.  Note that
            most servers propogate REMOVE as KICK to clients so it won't always
            work (the sole exception in testing this extension was Freenode).
            Defaults to True, because REMOVE is silly anyway.
        """
        # When overriding __init__, ALWAYS call the superclass! This sets up
        # the hook tables correctly and future-proofs you from other
        # initalisation that may be done in the base class.
        super().__init__(*args, **kwargs)

        # Read our configuration variables from kwargs.  You should always have
        # sane defaults.
        self.rejoin_delay = kwargs.pop('rejoin_delay', 5)
        self.rejoin_on_remove = kwargs.pop('rejoin_on_remove', True)

        # Keep a calendar, this way you will always know what rejoins are going
        # to fire.  (This is used to cancel all pending rejoins if we are
        # disconnected.)
        self.scheduled = {}

        if self.rejoin_on_remove:
            # This is used to ensure we know our part was voluntary
            self.parts = set()

    @hook("commands_out", "PART")
    def on_part_out(self, event):
        """ Command handler for PART's that are outgoing

        This is used to ensure we know when we PART a channel, it's voluntary.
        """
        if not self.rejoin_on_remove:
            # No bookkeeping
            return

        # This is how you can get another extension. In our case we retrieve
        # ISUPPORT, for dynamic discovery of valid channel types. Note that
        # these are case-sensitive.
        isupport = self.base.isupport

        # Now that we have it (and it's required so we don't have to check for
        # None), we can call methods from it. :D
        chantypes = isupport.get("CHANTYPES")

        # Parts are sent out as a comma-separated list
        for channel in event.line.params[0].split(","):
            if not channel.startswith(*chantypes):
                # Not a valid channel... we COULD cancel but that might break
                # some expectations of clients... so let's not :).
                continue

            # Casemap the channel according to the server's casemapping rules
            # Nicks and channels are case-insensitive, so always casemap them
            # for comparisons.
            channel = self.casefold(channel)

            self.parts.add(casefold)

    @hook("commands", "KICK")
    @hook("commands", "PART")
    def on_kick(self, event):
        """ Command handler for KICK and PART.

        This method receives a LineEvent object as its parameter, and will use
        it to determine if we were the ones kick/removed, and what action to
        take.
        """
        # Retrieve the BasicRFC extension handle.
        basicrfc = self.base.basic_rfc

        params = event.line.params

        # What channel were we kicked from?
        channel = self.casefold(params[0])

        # Determine if the kicked user is us.
        if self.casefold(params[1]) != self.casefold(basicrfc.nick):
            return  # It isn't us, so we don't care.

        if event.line.command == 'PART':
            # Do not rejoin if we are being 'nice'
            if not self.rejoin_on_remove:
                return
            elif channel in self.parts:
                # We left on our own :P
                self.parts.delete(channel)
                return

        if self.rejoin_on_remove:
            # Unconditionally remove channel.
            self.parts.discard(channel)

        # If we already pending rejoin, don't bother.
        # (XXX is this even possible?)
        # No not normally. But, always program defensively. --Elizabeth
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
        self.parts.discard(channel)
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
                pass  # Avoid a race when we get an exception during the join
                # callback.

        self.scheduled.clear()

# That's it!
# Pretty nifty, huh?  Now try it out!
