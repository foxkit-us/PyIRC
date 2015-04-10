#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


from PyIRC.extensions.basicrfc import BasicRFC
from PyIRC.extensions.autojoin import AutoJoin
from PyIRC.extensions.cap import CapNegotiate
from PyIRC.extensions.ctcp import CTCP
from PyIRC.extensions.isupport import ISupport
from PyIRC.extensions.lag import LagCheck
from PyIRC.extensions.sasl import SASLPlain
from PyIRC.extensions.starttls import StartTLS
from PyIRC.extensions.usertrack import UserTrack
from PyIRC.extensions.channeltrack import ChannelTrack
from PyIRC.extensions.serviceslogin import ServicesLogin


__all__ = [BasicRFC, AutoJoin, CapNegotiate, CTCP, ISupport, LagCheck,
           SASLPlain, StartTLS, UserTrack, ChannelTrack, ServicesLogin]


extensions_db = {cls.__name__ : cls for cls in __all__}


""" Baseline recommended extensions """
base_recommended = [BasicRFC, AutoJoin, CTCP, ISupport, LagCheck]


""" IRCv3 recommended extensions """
ircv3_recommended = base_recommended + [CapNegotiate, SASLPlain, StartTLS]


""" Recommended for bots """
bot_recommended = ircv3_recommended + [UserTrack, ChannelTrack]
