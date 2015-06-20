#!/usr/bin/env python3

from distutils.core import setup

setup(name="PyIRC",
      version="3.0a2",
      description="A Python IRC library",
      author="Elizabeth Myers",
      author_email="elizabeth@interlinked.me",
      url="https://elizafox.github.io/PyIRC",
      packages=["PyIRC", "PyIRC.extensions", "PyIRC.util", "PyIRC.io"],
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Developers",
          "Topic :: Communications :: Chat :: Internet Relay Chat",
          "Topic :: Internet",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Programming Language :: Python :: 3 :: Only",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Operating System :: OS Independent",
          "License :: DFSG approved",
      ]
      )
