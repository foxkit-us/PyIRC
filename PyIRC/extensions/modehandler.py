#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Mode handling components"""


from PyIRC.auxparse import mode_parse, prefix_parse
from PyIRC.extension import BaseExtension
from PyIRC.event import LineEvent, EventState
from PyIRC.hook import hook
from PyIRC.numerics import Numerics


class ModeEvent(LineEvent):

    """An event triggered upon mode changes."""

    def __init__(self, event, line, target, adding, mode, param=None):
        super().__init__(event, line)

        self.target = target
        self.adding = adding
        self.mode = mode
        self.param = param


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

        targiet = params.pop(0)
        modes = params.pop(0)

        if not target.startswith(*isupport.get("CHANTYPES")):
            # TODO - user modes
            return
        else:
            mode_call = None

        for mode, param, adding in mode_parse(modes, params, modegroups,
                                              prefix):
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
            self.call_event("modes", mode_call, line, target, adding, mode,
                            param)

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
                self.call_event("modes", "mode_prefix", line, target, True,
                                mode, nick)

