# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Formatting of IRC messages.

This module contains IRC formatting-related data, and reformatting classes to
deal with this formatting.

Bold, italic, underline, reverse, and colours are handled.
"""


try:
    from enum import Enum, IntEnum, unique
except ImportError:
    from PyIRC.util.enum import Enum, IntEnum, unique

from collections import namedtuple
from re import compile


class ColourRGB(namedtuple("ColourRGB", "red green blue")):

    """A colour triplet (red, green, and blue)"""

    @property
    def html(self):
        """Convert triplet to HTML format"""
        return "#{:02X}{:02X}{:02X}".format(self.red, self.green, self.blue)


class ColourEscape(namedtuple("ColourEscape", "intense base")):

    """Defines a new ANSI/VT100-style colour escape sequence"""

    @property
    def foreground(self):
        return self.base + 30

    @property
    def background(self):
        return self.base + 40


@unique
class Colour(IntEnum):

    """A list of colour numbers from name to index.

    mIRC maintains a list of `colour indexes to names`_.

    .. _colour indexes to names: http://www.mirc.com/colors.html
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


@unique
class ColourRGB(Enum):

    """Colours used on IRC, converted to RGB values.

    mIRC maintains a list_ of colour codes to values.

    .. _list: http://www.mirc.com/colors.html
    """

    white = ColourRGB(255, 255, 255)
    black = ColourRGB(0, 0, 0)
    blue = ColourRGB(0, 0, 127)
    green = ColourRGB(0, 147, 0)
    light_red = ColourRGB(255, 0, 0)
    brown = ColourRGB(127, 0, 0)
    purple = ColourRGB(156, 0, 156)
    orange = ColourRGB(252, 127, 0)
    yellow = ColourRGB(255, 255, 0)
    light_green = ColourRGB(0, 252, 0)
    cyan = ColourRGB(0, 147, 147)
    light_cyan = ColourRGB(0, 255, 255)
    light_blue = ColourRGB(0, 0, 252)
    pink = ColourRGB(255, 0, 255)
    grey = ColourRGB(127, 127, 127)
    light_grey = ColourRGB(210, 210, 210)


@unique
class ColourVT100(Enum):

    """Colours used on IRC, approximated with VT100/ANSI escapes."""

    white = ColourEscape(True, 7),
    black = ColourEscape(False, 0),
    blue = ColourEscape(False, 4),
    green = ColourEscape(False, 2)
    light_red = ColourEscape(True, 1)
    brown = ColourEscape(False, 1)
    purple = ColourEscape(False, 5)
    orange = ColourEscape(False, 3)
    yellow = ColourEscape(True, 3)
    light_green = ColourEscape(True, 2)
    cyan = ColourEscape(False, 6)
    light_cyan = ColourEscape(True, 6)
    light_blue = ColourEscape(True, 4)
    pink = ColourEscape(True, 5)
    grey = ColourEscape(True, 0)
    light_grey = ColourEscape(False, 7)


@unique
class FormattingCodes(Enum):

    """IRC formatting codes.

    A list is maintained by WikiChip_.

    .. _WikiChip: http://en.wikichip.org/wiki/irc/colors
    """

    bold = '\x02'
    colour = '\x03'  # Special because it uses fg[,bg]
    normal = '\x0f'
    reverse = '\x16'
    italic = '\x1d'
    underline = '\x1f'


class Formatter:

    """A basic format parser that uses callbacks to perform formatting.

    The callbacks return a string which is then added to the final output.

    :ivar bold:
        Set when text should be bold.

    :ivar colour:
        A (foreground, background) tuple; members not set are set to None.

    :ivar reverse:
        Set when colours are being reversed.

    :ivar italic:
        Set when text should be in italics.

    :ivar underline:
        Set when text should be underline.
    """

    # Used for matching colour codes
    cmatch = compile('^([0-9]+)(?:,([0-9]+)?)?')

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all colours.

        You should not need to override this."""
        self.bold = False
        self.colour = (None, None)
        self.reverse = False
        self.italic = False
        self.underline = False

    def format(self, string):
        """Convert a given IRC string.

        Returns the final formatted string.

        Special formatting is done by using callbacks. All callbacks are
        called after the state is updated to reflect the new status, except
        for normal which cannot work in any other way (due to needing to know
        what formatters to reset).

        :param string:
            String to reformat.
        """
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
        """Callback to do bold formatting"""
        raise NotImplementedError()

    def do_colour(self):
        """Callback to do colour formatting"""
        raise NotImplementedError()

    def do_normal(self):
        """Callback to remove all formatting"""
        raise NotImplementedError()

    def do_reverse(self):
        """Callback to do reversal formatting (reverse colours)"""
        raise NotImplementedError()

    def do_italic(self):
        """Callback to do italic formatting"""
        raise NotImplementedError()

    def do_underline(self):
        """Callback to do underline formatting"""
        raise NotImplementedError()


class NullFormatter(Formatter):

    """A stripping formatter that simply removes formatting"""

    do_bold = lambda self : ''
    do_colour = lambda self : ''
    do_normal = lambda self : ''
    do_reverse = lambda self : ''
    do_italic = lambda self : ''
    do_underline = lambda self : ''


class HTMLFormatter(Formatter):

    """A basic HTML IRC formatting class"""

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


class VT100Formatter(Formatter):

    """A VT100 IRC formatting class, suitable for Unix-style terminals"""

    # (end, begin) pairs where applicable
    fmt_normal = '0'
    fmt_bold = ('22', '1')
    fmt_italic = ('23', '3')
    fmt_underline = ('24', '4')
    fmt_reverse = '7'

    # Special
    fmt_resetcolour = ('39', '49')

    # ANSI SGR escape
    sgr = "\033[{}m"

    def do_bold(self):
        return self.sgr.format(self.fmt_bold[self.bold])

    def do_colour(self):
        ret = []
        if self.colour == (None, None):
            # restore background
            ret.extend(self.fmt_resetcolour)
            if self.bold:
                # restore bold
                ret.append(self.fmt_bold[1])
        else:
            fg = ColourVT100[self.colour[0].name].value
            bg = ColourVT100[self.colour[1].name].value

            if self.bold and not fg.intense:
                # conflicts -_-
                ret.append(self.fmt_bold[0])
            elif not self.bold and fg.intense:
                # intensify!
                ret.append(self.fmt_bold[1])

            # The time has come to.. colourise!
            ret.extend((str(fg.foreground), str(bg.background)))

        return self.sgr.format(';'.join(ret))

    def do_italic(self):
        # NB - not well supported!
        return self.sgr.format(self.fmt_italic[self.italic])

    def do_normal(self):
        return self.sgr.format(self.fmt_normal)

    def do_reverse(self):
        return self.sgr.format(self.fmt_reverse)

    def do_underline(self):
        return self.sgr.format(self.fmt_underline[self.underline])
