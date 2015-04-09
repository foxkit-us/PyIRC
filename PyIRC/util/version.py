# Copyright © 2013-2015 Andrew Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC3 project. See LICENSE in the root directory
# for licensing information.


try:
    import pkg_resources
except ImportError:
    pkg_resources = None

import subprocess

from collections import namedtuple


def _gitversion():
    try:
        command = ["git","log","-1","--pretty=format:%h"]
        return subprocess.check_output(command).decode()
    except (OSError, subprocess.SubprocessError):
        return "UNKNOWN"


major = 3
minor = 0
status = "alpha"
gitversion = _gitversion()

Version = namedtuple("Version", "major minor status gitversion")


""" Current PyIRC version

Attributes:
    major: Current major version. Set to 3 for PyIRC 3.
    minor: Current minor version.
    status: Release status (alpha, beta, release)
    gitversion: Current git revision, may be set to "unknown"
"""
version = Version(major, minor, status, gitversion)


def _versionstr():
    try:
        return pkg_resources.require("PyIRC")[0].version
    except Exception:
        return "{major}.{minor}-{status[0]}[{gitversion}]".format(**globals())


""" Current PyIRC version string, freeform. Obtained from the package whenever
possible, but may be generated from constants. """
versionstr = _versionstr()
