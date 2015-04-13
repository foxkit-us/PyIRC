# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Colour formatting constants

This includes bold, underline, (the somewhat widely supported) italic, and
colouration"""


try:
    from enum import Enum, IntEnum
except ImportError:
    from PyIRC.util.enum import Enum, IntEnum

from collections import namedtuple
from re import compile


class ColourTriplet(namedtuple("ColourTriplet", "red green blue")):
    """A colour triplet"""

    @property
    def html(self):
        """Convert triplet to HTML format"""
        return "#{:02X}{:02X}{:02X}".format(self.red, self.green, self.blue)


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


class Colour(IntEnum):
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
    italic = '\x1d'
    underline = '\x1f'


class Formatter:
    """A basic format parser that uses callbacks to perform formatting
    
    The callbacks return a string which is then added to the final output.
    """

    # Used for matching colour codes
    cmatch = compile('^([0-9]+)(?:,([0-9]+)?)?')

    def __init__(self):
        self.reset()

    def reset(self):
        self.bold = False
        self.colour = (None, None)
        self.reverse = False
        self.italic = False
        self.underline = False

    def format(self, string):
        ret = list()
        index = 0
        l = len(string)
        while index < l:
            char = string[index]

            # Check if char is a formatter
            if char == FormattingCodes.bold.value:
                self.bold = not self.bold
                ret.append(self.do_bold())

            elif char == FormattingCodes.colour.value:
                if self.colour != (None, None):
                    # Strip colours (even before a change)
                    self.colour = (None, None)
                    ret.append(self.do_colour())

                # Retrieve colour code
                if index + 1 > l:
                    # Not enough length for a colour
                    break

                match = self.cmatch.match(string[index + 1:])
                if not match:
                    # No colour here either...
                    index += 1
                    continue

                # Only 16 colours
                self.colour = tuple(Colour(int(c) % 16) for c in
                                    match.groups())
                index += match.end()

                ret.append(self.do_colour())
            
            elif char == FormattingCodes.normal.value:
                # Reset all /after/ for normal formatters, so callbacks know
                # what to undo.
                ret.append(self.do_normal())
                self.reset()
            
            elif char == FormattingCodes.reverse.value:
                self.reverse = not self.reverse
                ret.append(self.do_reverse())
            
            elif char == FormattingCodes.italic.value:
                self.italic = not self.italic
                ret.append(self.do_italic())
            
            elif char == FormattingCodes.underline.value:
                self.underline = not self.underline
                ret.append(self.do_underline())
            
            else:
                # No formatter
                ret.append(char)

            index += 1

        ret.append(self.do_normal())
        self.reset()
        return ''.join(ret)

    def do_bold(self):
        raise NotImplementedError()

    def do_colour(self):
        raise NotImplementedError()

    def do_normal(self):
        raise NotImplementedError()

    def do_reverse(self):
        raise NotImplementedError()

    def do_italic(self):
        raise NotImplementedError()

    def do_underline(self):
        raise NotImplementedError()


class HTMLFormatter(Formatter):
    def do_bold(self):
        return '<b>' if self.bold else '</b>'

    def do_colour(self):
        if self.colour == (None, None):
            return "</span>"

        string = "<span style=\""
        if self.colour[0] != None:
            value = ColourRGB[self.colour[0].name].value.html
            string += 'color:{};'.format(value)
        if self.colour[1] != None:
            value = ColourRGB[self.colour[1].name].value.html
            string += 'background-color:{};'.format(value)

        string += "\">"

        return string

    def do_italic(self):
        return "<i>" if self.italic else "</i>"

    def do_normal(self):
        ret = []
        if self.bold:
            ret.append("</b>")
        if self.colour != (None, None):
            ret.append("</span>")
        if self.italic:
            ret.append("</i>")
        if self.underline:
            ret.append("</u>")

        return ''.join(ret)

    def do_reverse(self):
        if self.reverse:
            return "<span style=\"filter: invert(100%);" \
                "-webkit-filter: invert(100%);\">"
        else:
            return "</span>"

    def do_underline(self):
        return "<u>" if self.underline else "</u>"
