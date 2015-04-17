#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Extensions bundled with PyIRC.

These are the actual things that make PyIRC do things. They implement various
commands and allow new features to be easily added to the library in a
backwards-compatible way."""


from PyIRC.extensions.basicrfc import BasicRFC
from PyIRC.extensions.autojoin import AutoJoin
from PyIRC.extensions.cap import CapNegotiate
from PyIRC.extensions.ctcp import CTCP
from PyIRC.extensions.isupport import ISupport
from PyIRC.extensions.kickrejoin import KickRejoin
from PyIRC.extensions.lag import LagCheck
from PyIRC.extensions.sasl import SASLPlain
from PyIRC.extensions.starttls import StartTLS
from PyIRC.extensions.usertrack import UserTrack
from PyIRC.extensions.channeltrack import ChannelTrack
from PyIRC.extensions.services import ServicesLogin
from PyIRC.extensions.bantrack import BanTrack


__all__ = ["basicrfc", "autojoin", "cap", "ctcp", "isupport", "kickrejoin",
           "lag", "sasl", "starttls", "usertrack", "channeltrack", "services",
           "bantrack"]


__all_cls__ = [BasicRFC, AutoJoin, CapNegotiate, CTCP, ISupport, KickRejoin,
               LagCheck, SASLPlain, StartTLS, UserTrack, ChannelTrack,
               ServicesLogin, BanTrack]


"""A reference of all extensions by name"""
extensions_db = {cls.__name__ : cls for cls in __all_cls__}


"""Basic recommended extensions that are compatible with most servers"""
base_recommended = [BasicRFC, AutoJoin, CTCP, ISupport, LagCheck]


"""Recommended extensions for use with IRCv3 compliant servers """
ircv3_recommended = base_recommended + [CapNegotiate, SASLPlain, StartTLS]


"""Recommended extensions for bots"""
bot_recommended = ircv3_recommended + [UserTrack, ChannelTrack]
