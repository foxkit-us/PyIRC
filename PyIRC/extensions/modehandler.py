#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Mode handling components"""


from time import time


from PyIRC.auxparse import mode_parse, prefix_parse
from PyIRC.extension import BaseExtension
from PyIRC.event import LineEvent, EventState
from PyIRC.hook import hook
from PyIRC.numerics import Numerics


class ModeEvent(LineEvent):

    """An event triggered upon mode changes."""

    def __init__(self, event, line, setter, target, adding, mode, param=None,
                 timestamp=None):
        """Initalise the ModeEvent instance.

        Arguments:

        :param event:
            The event fired

        :param line:
            The :py:class:`~PyIRC.line.Line` instance of the firing mode.

        :param setter:
            The :py:class:`~PyIRC.line.Hostmask` of the setter of this mode,
            or ``None`` when unknown.

        :param target:
            The target of this command, as a regular string.

        :param adding:
            Set to ``True`` if the mode is being added to the target, or
            ``False`` if being removed. Consumers should be prepared for
            redundant modes, as many IRC daemons do not do strict checking
            for performance reasons.

        :param mode:
            The mode being set or unset.

        :param param:
            The parameter of the mode, set to ``None`` for most modes.

        :param timestamp:
            The time this mode was set. If None, the current system time will
            be used.
        """
        super().__init__(event, line)

        self.setter = setter
        self.target = target
        self.adding = adding
        self.mode = mode
        self.param = param
        self.timestamp = timestamp if timestamp else round(time())


class ModeHandler(BaseExtension):

    """An extension that handles mode changes and emits events."""

    requires = ["BasicRFC", "ISupport"]

    hook_classes = {
        "modes": ModeEvent
    }

    @hook("commands", Numerics.RPL_CHANNELMODEIS)
    @hook("commands", "MODE")
    def mode(self, event):
        # Offer an easy to use interface for mode
        isupport = self.get_extension("ISupport")
        modegroups = isupport.get("CHANMODES")
        prefix = prefix_parse(isupport.get("PREFIX"))

        line = event.line
        params = list(line.params)
        if line.command == Numerics.RPL_CHANNELMODEIS.value:
            params.pop(0)

        target = params.pop(0)
        modes = params.pop(0)

        if not target.startswith(*isupport.get("CHANTYPES")):
            # TODO - user modes
            return

        gen = mode_parse(modes, params, modegroups, prefix)
        prefix = prefix[0]
        for mode, param, adding in gen:
            if mode in prefix:
                mode_call = "mode_prefix"
            elif mode in modegroups[0]:
                mode_call = "mode_list",
            elif mode in modegroups[1]:
                mode_call = "mode_key",
            elif mode in modegroups[2]:
                mode_call = "mode_param",
            else:
                mode_call = "mode_normal"

            # TODO - aggregation
            self.call_event("modes", mode_call, line, line.hostmask, target,
                            adding, mode, param)

    @hook("commands", Numerics.RPL_NAMREPLY)
    def names(self, event):
        line = event.line
        params = line.params

        target = params[2]

        isupport = self.get_extension("ISupport")
        prefix = prefix_parse(isupport.get("PREFIX"))

        for nick in params[-1].split():
            modes, nick = status_prefix_parse(nick, prefix)

            for mode in modes:
                # TODO - aggregation
                self.call_event("modes", "mode_prefix", line, line.hostmask,
                                target, True, mode, nick)

    @hook("commands", Numerics.RPL_BANLIST)
    def ban_list(self, event):
        return self.handle_list(event, 'b')

    @hook("commands", Numerics.RPL_EXCEPTLIST)
    def except_list(self, event):
        return self.handle_list(event, 'e')

    @hook("commands", Numerics.RPL_INVITELIST)
    def invite_list(self, event):
        return self.handle_list(event, 'I')

    @hook("commands", Numerics.RPL_QUIETLIST)
    def quiet_list(self, event):
        isupport = self.get_extension("ISupport")
        if 'q' in isupport.get("PREFIX"):
            logger.critical("Got a quiet mode, but mode for quiet is " \
                            "unknown to us!")
            logger.critical("Please report a bug to the PyIRC team with " \
                            "the mode your IRC daemon uses, along with its " \
                            "version information")
            return

        return self.handle_list(event, 'q')

    @hook("commands", Numerics.RPL_SPAMFILTERLIST)
    def spamfilter_list(self, event):
        return self.handle_list(event, 'g')

    @hook("commands", Numerics.RPL_EXEMPTCHANOPSLIST)
    def exemptchanops_list(self, event):
        return self.handle_list(event, 'X')

    @hook("commands", Numerics.RPL_AUTOOPLIST)
    def autoop_list(self, event):
        return self.handle_list(event, 'w')

    @hook("commands", Numerics.RPL_REOPLIST)
    def reop_list(self, event):
        return self.handle_list(event, 'R')

    def handle_list(self, event, mode):
        line = event.line
        params = line.params

        try:
            target = params[1]
            mask = params[2]
            if len(params) > 3:
                setter = Hostmask(params[3])
                if len(params) > 4:
                    timestamp = int(params[4])
            else:
                setter = line.hostmask
                timestamp = None
        except Exception:
            logger.warning("Bogus list mode received: %s", mode)
            return

        self.call_event("modes", "mode_list", line, setter, target, True,
                        mode, mask, timestamp)

