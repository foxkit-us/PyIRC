# Copyright © 2015 A. Wilcox and Elizabeth Myers.
# All rights reserved.
# This file is part of the PyIRC 3 project. See LICENSE in the root directory
# for licensing information.


"""Test proper channel tracking implementation."""


from time import time

import unittest

from PyIRC.line import Line, Hostmask
from PyIRC.numerics import Numerics
from test_helpers import new_conn_with_handshake, conn_mask


def join_line(irc, name):
    """Helper: Construct a JOIN line.

    :param irc:
        The IRC ocnnection.

    :param name:
        The channel name.
    """

    return Line(hostmask=conn_mask(irc), command='JOIN', params=(name,))


def rpl_topic_line(irc, name, topic):
    """Helper: Construct an RPL_TOPIC line.

    :param irc:
        The IRC connection.

    :param name:
        The channel name.

    :param topic:
        The topic.
    """

    return Line(hostmask=':nonexistent.test.server',
                command=Numerics.RPL_TOPIC.value,
                params=(irc.nick, name, topic))


def rpl_topiwhotime_line(irc, name, setter, set_on):
    """Helper: Construct an RPL_TOPICWHOTIME line.

    :param irc:
        The IRC connection.

    :param name:
        The channel name.

    :param setter:
        The setter of the topic (str or Hostmask).

    :param set_on:
        The timestamp (str or int).
    """

    return Line(hostmask=':nonexistent.test.server',
                command=Numerics.RPL_TOPICWHOTIME.value,
                params=(irc.nick, name, str(setter), str(set_on)))


class TestChannelTrackBehaviour(unittest.TestCase):
    """Test the behaviour of the ChannelTrack extension."""

    def setUp(self):
        """Set up the default slot that sets self.channel and such."""
        extensions = ['BasicRFC', 'BaseTrack', 'ChannelTrack']
        self.connection = new_conn_with_handshake(extensions=extensions)

        def handler(caller, channel):
            self.channel = channel

        event = ('channel', 'channel_create')
        self.connection.signals.get_signal(event).add(handler)

    def assertTopicEqual(self, topic, setter, set_on):
        self.assertEqual(self.channel.topic, topic, 'Topic is wrong')
        self.assertTrue(self.channel.topicwho.match(str(setter)),
                        'Setter is wrong')
        self.assertEqual(self.channel.topictime, set_on, 'Topic time is wrong')

    def test_channel_create_event(self):
        """Ensure the (channel, channel_create) event is fired correctly."""
        name = '#Test'
        self.handler_called = False

        def handler(caller, channel):
            self.assertEquals(channel.name, name, 'Channel name is wrong')
            self.handler_called = True

        irc = self.connection
        irc.signals.get_signal(('channel', 'channel_create')).add(handler)
        irc.inject_line(join_line(irc, name))
        self.assertTrue(self.handler_called, 'Handler was not called')

    def test_channel_topic_server_user(self):
        """Ensure topic sent from server, set by user, is handled correctly."""

        name = '#gentoo-python'
        topic = 'Set e.g. PYTHON_TARGETS="python2_7 python3_2 python3_3 '\
                'python3_4" in /etc/make.conf if you want to install Python '\
                'modules for multiple Python versions. | '\
                'http://www.gentoo.org/proj/en/Python/#doc_chap5'
        setter = Hostmask(nick='xiaomiao', username='~purrrr',
                          host='gentoo/developer/bonsaikitten')
        set_on = 1404711155

        irc = self.connection
        irc.inject_line(join_line(irc, name))
        irc.inject_line(rpl_topic_line(irc, name, topic))
        irc.inject_line(rpl_topiwhotime_line(irc, name, setter, set_on))

        self.assertTopicEqual(topic, setter, set_on)

    def test_channel_topic_server_server(self):
        """Ensure topic sent from and set by server is handled correctly."""
        name = '#help'
        topic = 'Official help channel | To register a nick : /msg NickServ '\
                'help register | To group a nick, /msg nickserv help group | '\
                'Lost password? /msg nickserv SENDPASS <accountname> | State '\
                'your question and people will answer eventually (It might '\
                'take 10 or so minutes)'
        setter = 'chrysalis.server'
        set_on = 1395559296

        irc = self.connection
        irc.inject_line(join_line(irc, name))
        irc.inject_line(rpl_topic_line(irc, name, topic))
        irc.inject_line(rpl_topiwhotime_line(irc, name, setter, set_on))

        self.assertTopicEqual(topic, Hostmask(host=setter), set_on)

    def test_channel_topic_user(self):
        """Ensure topic set by user is handled correctly."""
        name = '#Sporks'
        topic = "#Sporks - we'll bring yo dick"
        setter = Hostmask(nick='lstarnes', username='~lucius',
                          host='interlinked/netadmin/automaton/lstarnes')
        set_on = int(time())  # 1437288043

        irc = self.connection
        irc.inject_line(join_line(irc, name))
        irc.inject_line(Line(hostmask=setter, command='TOPIC',
                             params=(name, topic)))

        self.assertTopicEqual(topic, setter, set_on)

    def test_channel_no_topic(self):
        """Ensure channels with no topic are handled correctly."""
        name = '#test'

        irc = self.connection
        irc.inject_line(join_line(irc, name))
        self.assertIsNone(self.channel.topic)

        irc.inject_line(Line(hostmask='nonexistent.test.server',
                             command=Numerics.RPL_NOTOPIC,
                             params=(irc.nick, name)))
        self.assertIsNotNone(self.channel.topic)
