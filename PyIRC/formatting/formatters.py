# Copyright © 2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""IRC message formatting classes.

This module contains reformatting classes to handle IRC formatting codes.

Bold, italic, underline, reverse, and colours are handled.

"""


try:
    from enum import Enum, unique
except ImportError:
    from PyIRC.util.enum import Enum, unique

import re

from PyIRC.formatting.colours import (Colours, ColoursRGB, ColoursANSI,
                                      ColoursXTerm256)


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

    :ivar foreground:
        The present foreground colour. When unset, it is set to None.

    :ivar background:
        The present background colour. When unset, it is set to None.

    :ivar reverse:
        Set when colours are being reversed.

    :ivar italic:
        Set when text should be in italics.

    :ivar underline:
        Set when text should be underline.

    """

    # Used for matching colour codes
    cmatch = re.compile('^([0-9]+)(?:,([0-9]+)?)?')

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all colours.

        You should not need to override this.

        """
        self.bold = False
        self.foreground = None
        self.background = None
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
        # We have to do this because reset is not __init__
        # (but they are still technically defined in __init__)
        # pylint: disable=attribute-defined-outside-init
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
                if self.foreground or self.background:
                    # Strip colours (even before a change)
                    self.foreground = self.background = None
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
                self.foreground = (Colours(int(match.group(1)) % 16)
                                   if match.group(1) is not None else None)
                self.background = (Colours(int(match.group(2)) % 16)
                                   if match.group(2) is not None else None)
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
        """Callback to do bold formatting."""
        raise NotImplementedError()

    def do_colour(self):
        """Callback to do colour formatting."""
        raise NotImplementedError()

    def do_normal(self):
        """Callback to remove all formatting."""
        raise NotImplementedError()

    def do_reverse(self):
        """Callback to do reversal formatting (reverse colours)"""
        raise NotImplementedError()

    def do_italic(self):
        """Callback to do italic formatting."""
        raise NotImplementedError()

    def do_underline(self):
        """Callback to do underline formatting."""
        raise NotImplementedError()


class NullFormatter(Formatter):

    """A stripping formatter that simply removes formatting."""

    do_bold = lambda self: ''
    do_colour = lambda self: ''
    do_normal = lambda self: ''
    do_reverse = lambda self: ''
    do_italic = lambda self: ''
    do_underline = lambda self: ''


class HTMLFormatter(Formatter):

    """A basic HTML IRC formatting class."""

    def do_bold(self):
        return '<b>' if self.bold else '</b>'

    def do_colour(self):
        if not (self.background or self.foreground):
            return "</span>"

        string = "<span style=\""
        if self.foreground is not None:
            value = ColoursRGB[self.foreground.name].value.html
            string += 'color:{};'.format(value)
        if self.background is not None:
            value = ColoursRGB[self.background.name].value.html
            string += 'background-color:{};'.format(value)

        string += "\">"

        return string

    def do_italic(self):
        return "<i>" if self.italic else "</i>"

    def do_normal(self):
        ret = []
        if self.bold:
            ret.append("</b>")
        if self.foreground or self.background:
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


class ANSIFormatter(Formatter):

    """An ANSI IRC formatting class, useful as a generic terminal class.

    This is mostly for a portable, lowest-common-denominator formatter. You
    will probably want a better formatter than this.

    8 colours are supported; some colours are emulated with bold.
    """

    # (end, begin) pairs where applicable
    fmt_normal = '0'
    fmt_bold = ('22', '1')
    fmt_italic = ('23', '3')
    fmt_underline = ('24', '4')
    fmt_reverse = '7'

    # Special
    fmt_resetforeground = '39'
    fmt_resetbackground = '49'

    # ANSI SGR escape
    sgr = "\033[{}m"

    def do_bold(self):
        return self.sgr.format(self.fmt_bold[self.bold])

    def do_colour(self):
        ret = []
        if not (self.foreground and self.background):
            # restore background
            ret.extend((self.fmt_resetforeground, self.fmt_resetbackground))
            if self.bold:
                # restore bold if needed
                ret.append(self.fmt_bold[1])
            else:
                # reset bold if needed
                ret.append(self.fmt_bold[0])
        else:
            if self.foreground is not None:
                fg = ColoursANSI[self.foreground.name].value

                if self.bold and not fg.intense:
                    # conflicts -_-
                    ret.append(self.fmt_bold[0])
                elif not self.bold and fg.intense:
                    # intensify!
                    ret.append(self.fmt_bold[1])

                ret.append(str(fg.foreground))
            else:
                # Reset the foreground
                ret.append(self.fmt_resetforeground)
                if self.bold:
                    # Restore bold
                    ret.append(self.fmt_bold[1])

            if self.background is not None:
                bg = ColoursANSI[self.background.name].value

                ret.append(str(bg.background))
            else:
                ret.append(self.fmt_resetbackground)

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


VT100Formatter = ANSIFormatter
"""Deprecated alias."""


class XTerm16ColourFormatter(ANSIFormatter):

    """Like the :py:class:`~PyIRC.formatting.formatters.ANSIFormatter`, but
    for XTerm. Most other terminals support this, excluding Windows."""

    def do_colour(self):
        ret = []
        if not (self.foreground and self.background):
            # Restore background like ANSI, sans bold fixing
            ret.extend((self.fmt_resetforeground, self.fmt_resetbackground))
        else:
            if self.foreground is not None:
                fg = ColoursANSI[self.foreground.name].value
                ret.append(str(fg.foreground_16))
            else:
                # Reset foreground just in case
                ret.append(self.fmt_resetforeground)

            if self.background is not None:
                bg = ColoursANSI[self.background.name].value
                ret.append(str(fg.background_16))
            else:
                # Reset background just in case
                ret.append(self.fmt_resetbackground)

        return self.sgr.format(';'.join(ret))


class XTerm256ColourFormatter(ANSIFormatter):

    """Like the :py:class:`~PyIRC.formatting.formatters.ANSIFormatter`, but
    for XTerm. Numerous other terminals support this."""

    format_bg = ('38', '5')
    format_fg = ('48', '5')

    def do_colour(self):
        ret = []
        if not (self.foreground and self.background):
            # Restore background like ANSI, sans bold fixing
            ret.extend((self.fmt_resetforeground, self.fmt_resetbackground))
        else:
            if self.foreground is not None:
                ret.extend(self.format_fg)
                colour = ColoursXTerm256[self.foreground.name].value
                ret.append(str(colour))
            else:
                # Reset foreground just in case
                ret.append(self.fmt_resetforeground)

            if self.background is not None:
                ret.extend(self.format_bg)
                colour = ColoursXTerm256[self.background.name].value
                ret.append(str(colour))
            else:
                # Reset background just in case
                ret.append(self.fmt_resetbackground)

        return self.sgr.format(';'.join(ret))


class XTermTrueColourFormatter(ANSIFormatter):

    """Like the :py:class:`~PyIRC.formatting.formatters.ANSIFormatter`, but
    for XTerm.

    This features true-colour fidelity in many terminals (in XTerm, it will
    use the nearest colour). This gives the best results.
    """

    format_bg = ('48', '2')
    format_fg = ('38', '2')

    def do_colour(self):
        ret = []
        if not (self.foreground and self.background):
            # Restore background like ANSI, sans bold fixing
            ret.extend((self.fmt_resetforeground, self.fmt_resetbackground))
        else:
            if self.foreground is not None:
                ret.extend(self.format_fg)
                colour = ColoursRGB[self.foreground.name].value
                ret.append(str(colour.red))
                ret.append(str(colour.green))
                ret.append(str(colour.blue))
            else:
                # Reset foreground just in case
                ret.append(self.fmt_resetforeground)

            if self.background is not None:
                ret.extend(self.format_bg)
                colour = ColoursRGB[self.background.name].value
                ret.append(str(colour.red))
                ret.append(str(colour.green))
                ret.append(str(colour.blue))
            else:
                # Reset background just in case
                ret.append(self.fmt_resetbackground)

        return self.sgr.format(';'.join(ret))
