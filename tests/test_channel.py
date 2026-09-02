"""Tests for channel-name normalisation.

Servers will not find a channel typed without its prefix. Run with:

    python -m unittest discover -s tests -v
"""

import unittest

from test_security import lb


class NormalizeChannel(unittest.TestCase):
    def test_a_bare_name_gains_a_hash(self):
        self.assertEqual(lb.normalize_channel("casale"), "#casale")

    def test_an_existing_hash_is_left_alone(self):
        self.assertEqual(lb.normalize_channel("#casale"), "#casale")

    def test_the_other_valid_prefixes_are_left_alone(self):
        for name in ("&local", "+modeless", "!11ABCsafe"):
            self.assertEqual(lb.normalize_channel(name), name)

    def test_surrounding_whitespace_is_stripped(self):
        self.assertEqual(lb.normalize_channel("  casale  "), "#casale")
        self.assertEqual(lb.normalize_channel("  #casale "), "#casale")

    def test_empty_stays_empty(self):
        """A bare '#' is not a channel, so do not invent one."""
        for value in ("", "   ", None):
            self.assertEqual(lb.normalize_channel(value), "")

    def test_a_hash_inside_the_name_is_not_a_prefix(self):
        self.assertEqual(lb.normalize_channel("chan#nel"), "#chan#nel")


class BotStoresTheNormalisedName(unittest.TestCase):
    def test_constructor_normalises(self):
        bot = lb.IRCBot("s", 6667, "localBot", "casale", "pw")
        self.assertEqual(bot.channel, "#casale")

    def test_channel_scoping_then_matches_the_server(self):
        """The real payoff: without this the channel check never matched."""
        bot = lb.IRCBot("s", 6667, "localBot", "casale", "pw")
        self.assertTrue(bot.is_channel(bot.channel))
        self.assertEqual(bot.channel.lower(), "#casale")


class PrefixSetsAgree(unittest.TestCase):
    """normalize_channel and is_channel must not drift apart: is_channel is
    what stops a channel being ignored or charged an abuse strike."""

    def test_every_prefix_is_recognised_and_left_unnormalised(self):
        bot = lb.IRCBot.__new__(lb.IRCBot)
        for prefix in lb.CHANNEL_PREFIXES:
            name = f"{prefix}chan"
            self.assertTrue(bot.is_channel(name), f"{name} not recognised")
            self.assertEqual(lb.normalize_channel(name), name)

    def test_a_normalised_name_is_always_recognised(self):
        bot = lb.IRCBot.__new__(lb.IRCBot)
        self.assertTrue(bot.is_channel(lb.normalize_channel("casale")))


if __name__ == "__main__":
    unittest.main()
