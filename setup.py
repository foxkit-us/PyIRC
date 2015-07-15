#!/usr/bin/env python3

from setuptools import setup

long_description = (
      """This is PyIRC, an IRC library designed to be flexible, extensible,
      well- documented, and easy to use. It is aimed at not only beginners
      and those who don't want to spend too much time writing boilerplate to
      get something going¸ but also the advanced user who knows exactly what
      they're doing."""
)

setup(name="PyIRC",
      version="3.0a3",
      description="A Python IRC library",
      long_description=long_description,
      keywords="IRC chat development",
      author="Elizabeth Myers",
      author_email="elizabeth@interlinked.me",
      url="https://elizafox.github.io/PyIRC",
      packages=["PyIRC", "PyIRC.extensions", "PyIRC.util", "PyIRC.io"],
      install_requires=["taillight >= 0.2b3"],
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
