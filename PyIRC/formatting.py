# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Colour formatting constants

This includes bold, underline, (the somewhat widely supported) italics, and
colouration"""


try:
    from enum import Enum
except ImportError:
    from PyIRC.util.enum import Enum

from collections import namedtuple


"""A colour triplet"""
ColourTriplet = ("ColourTriplet", "red green blue")


class ColourRGB(Enum):
    """Colour codes used on IRC, converted to RGB values
    
    mIRC maintains a list_ of colour codes to values.

    .. _list: http://www.mirc.com/colors.html
    """

    white = ColourTriplet(255, 255, 255)
    black = ColourTriplet(0, 0, 0)
    blue = ColourTriplet(0, 0, 127)
    green = ColourTriplet(0, 147, 0)
    light_red = ColourTriplet(255, 0, 0)
    brown = ColourTriplet(127, 0, 0)
    purple = ColourTriplet(156, 0, 156)
    orange = ColourTriplet(252, 127, 0)
    yellow = ColourTriplet(255, 255, 0)
    light_green = ColourTriplet(0, 252, 0)
    cyan = ColourTriplet(0, 147, 147)
    light_cyan = ColourTriplet(0, 255, 255)
    light_blue = ColourTriplet(0, 0, 252)
    pink = ColourTriplet(255, 0, 255)
    grey = ColourTriplet(127, 127, 127)
    light_grey = ColourTriplet(210, 210, 210)


class ColourNum(Enum):
    """A list of colour numbers from name to index

    mIRC maintains a list_ of colour indexes to names

    .. _list: http://www.mirc.com/colors.html
    """

    white = 0
    black = 1
    blue = 2
    green = 3
    light_red = 4
    brown = 5
    purple = 6
    orange = 7
    yellow = 8
    light_green = 9
    cyan = 10
    light_cyan = 11
    light_blue = 12
    pink = 13
    grey = 14
    light_grey = 15


class FormattingCodes(Enum):
    """IRC formatting codes

    A list is maintained by WikiChip_

    .. _WikiChip: http://en.wikichip.org/wiki/irc/colors
    """

    bold = '\x02'
    colour = '\x03'  # Special because it uses fg[,bg]
    normal = '\x0f'
    reverse = '\x16'
    italics = '\x1d'
    underline = '\x1f'
