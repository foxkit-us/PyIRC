#!/usr/bin/env python3
# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.

from PyIRC.base import BasicRFC

from PyIRC.extensions.autojoin import AutoJoin
from PyIRC.extensions.cap import CapNegotiate
from PyIRC.extensions.ctcp import CTCP
from PyIRC.extensions.isupport import ISupport
from PyIRC.extensions.lag import LagCheck
from PyIRC.extensions.sasl import SASLPlain
from PyIRC.extensions.starttls import STARTTLS


""" Baseline recommended extensions """
base_recommended = [BasicRFC, AutoJoin, CTCP, ISupport, LagCheck]

""" IRCv3 recommended extensions """
ircv3_recommended = base_recommended + [CapNegotiate, SASLPlain, STARTTLS]
