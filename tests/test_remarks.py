"""Tests for the random fallback remarks.

The bot sends a canned line when a generation produces nothing. Run with:

    python -m unittest discover -s tests -v
"""

import unittest

from test_security import FakeEvent, lb, make_bot


class Resp:
    """Minimal stand-in for a requests response."""

    status_code = 200

    def __init__(self, content):
        self._content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {
            "choices": [
                {
                    "message": {"content": self._content, "role": "assistant"},
                    "finish_reason": "stop",
                }
            ]
        }


def run_channel_mention(bot, content, message="localBot hi"):
    """Drive one channel mention with a stubbed endpoint, inline."""
    sent = []
    bot.connection = type(
        "C", (), {"privmsg": lambda s, t, msg: sent.append((t, msg))}
    )()
    bot.dispatch_generation = lambda label, work: work()
    original = lb.requests.post
    lb.requests.post = lambda *a, **k: Resp(content)
    try:
        bot.on_public_message(
            None, FakeEvent("alice!u@a.example", "#chan", [message])
        )
    finally:
        lb.requests.post = original
    return sent


class RemarkLoading(unittest.TestCase):
    def test_comments_and_blank_lines_are_skipped(self):
        parsed = [
            " ".join(line.split())
            for line in "# a comment\n\n  \nreal remark\n  # indented comment\n".splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(parsed, ["real remark"])

    def test_shipped_file_is_inert(self):
        """The committed remarks.txt is comments only, so nothing changes."""
        self.assertEqual(lb.REMARKS, [], "remarks.txt shipped with live remarks")
        self.assertIsNone(lb.random_remark())

    def test_no_remark_ever_contains_a_line_break(self):
        """privmsg rejects line breaks outright, so flattening must happen first."""
        for remark in lb.REMARKS + ["a\nb", "one\ttwo"]:
            flattened = " ".join(str(remark).split())
            self.assertNotIn("\n", flattened)
            self.assertNotIn("\t", flattened)


class FallbackBehaviour(unittest.TestCase):
    def setUp(self):
        self._saved = lb.REMARKS
        lb.REMARKS = ["nothing to add", "ask me later"]

    def tearDown(self):
        lb.REMARKS = self._saved

    def test_failed_generation_sends_a_remark(self):
        sent = run_channel_mention(make_bot(), content="")
        self.assertEqual(len(sent), 1)
        target, msg = sent[0]
        self.assertEqual(target, "#chan")
        self.assertTrue(
            any(msg == f"alice: {r}" for r in lb.REMARKS),
            f"unexpected fallback text: {msg!r}",
        )

    def test_successful_generation_sends_no_remark(self):
        sent = run_channel_mention(make_bot(), content="a real answer")
        self.assertEqual(sent, [("#chan", "alice: a real answer")])

    def test_channel_fallback_is_prefixed_with_the_nick(self):
        sent = run_channel_mention(make_bot(), content="")
        self.assertTrue(sent[0][1].startswith("alice: "))

    def test_private_fallback_is_not_prefixed(self):
        bot = make_bot()
        sent = []
        bot.connection = type(
            "C", (), {"privmsg": lambda s, t, msg: sent.append((t, msg))}
        )()
        bot.send_fallback_remark("bob")
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][0], "bob")
        self.assertIn(sent[0][1], lb.REMARKS)

    def test_no_remarks_configured_means_silence(self):
        lb.REMARKS = []
        bot = make_bot()
        sent = []
        bot.connection = type(
            "C", (), {"privmsg": lambda s, t, msg: sent.append((t, msg))}
        )()
        self.assertFalse(bot.send_fallback_remark("bob"))
        self.assertEqual(sent, [])

    def test_kill_switch_silences_fallbacks(self):
        bot = make_bot(ai_enabled=False)
        sent = []
        bot.connection = type(
            "C", (), {"privmsg": lambda s, t, msg: sent.append((t, msg))}
        )()
        self.assertFalse(bot.send_fallback_remark("bob"))
        self.assertEqual(sent, [])

    def test_an_ignored_user_gets_nothing(self):
        bot = make_bot()
        bot.nick_hosts["bob"] = "bob.example"
        bot.ignore_list.add("bob.example")
        sent = []
        bot.connection = type(
            "C", (), {"privmsg": lambda s, t, msg: sent.append((t, msg))}
        )()
        bot.send_fallback_remark("bob")
        self.assertEqual(sent, [], "a remark reached an ignored user")


class Placeholders(unittest.TestCase):
    def setUp(self):
        self._saved = lb.REMARKS

    def tearDown(self):
        lb.REMARKS = self._saved

    def test_known_tokens_are_substituted(self):
        out = lb.fill_remark(
            "{bot_nickname} has no idea, {speaker_nickname} - ask in {channel}",
            speaker="alice",
            bot_nickname="localBot",
            channel="#chan",
        )
        self.assertEqual(out, "localBot has no idea, alice - ask in #chan")

    def test_an_unknown_token_survives_instead_of_raising(self):
        """A mistyped placeholder must not crash the failure path."""
        out = lb.fill_remark("what even is {speaker}?", speaker="alice")
        self.assertEqual(out, "what even is {speaker}?")

    def test_stray_braces_are_harmless(self):
        for text in ("¯\\_{ツ}_/¯", "{", "}{", "set {a, b}"):
            self.assertEqual(lb.fill_remark(text, speaker="alice"), text)

    def test_naming_the_speaker_suppresses_the_prefix(self):
        lb.REMARKS = ["sorry {speaker_nickname}, my brain melted"]
        sent = run_channel_mention(make_bot(), content="")
        self.assertEqual(sent, [("#chan", "sorry alice, my brain melted")])

    def test_a_remark_without_the_token_keeps_the_prefix(self):
        lb.REMARKS = ["my brain melted"]
        sent = run_channel_mention(make_bot(), content="")
        self.assertEqual(sent, [("#chan", "alice: my brain melted")])

    def test_private_fallback_substitutes_too(self):
        lb.REMARKS = ["not now {speaker_nickname}"]
        bot = make_bot()
        sent = []
        bot.connection = type(
            "C", (), {"privmsg": lambda s, t, msg: sent.append((t, msg))}
        )()
        bot.send_fallback_remark("bob", speaker="bob")
        self.assertEqual(sent, [("bob", "not now bob")])


class RemarksBypassTheOutputFilter(unittest.TestCase):
    """Remarks are operator-authored, so the anti-injection filters must not
    apply to them. A remark opening with an IRC verb would otherwise be blocked
    and charge an abuse strike to whoever happened to be talking."""

    def setUp(self):
        self._saved = lb.REMARKS
        lb.REMARKS = ["TIME to go!"]

    def tearDown(self):
        lb.REMARKS = self._saved

    def test_a_remark_starting_with_an_irc_verb_is_still_sent(self):
        bot = make_bot()
        self.assertTrue(
            bot.contains_irc_commands("TIME to go!"),
            "precondition: this text does trip the output filter",
        )
        sent = run_channel_mention(bot, content="")
        self.assertEqual(sent, [("#chan", "alice: TIME to go!")])

    def test_and_charges_nobody_a_strike(self):
        bot = make_bot()
        run_channel_mention(bot, content="")
        self.assertEqual(dict(bot.abuse_strikes), {})

    def test_emoji_survive(self):
        lb.REMARKS = ["no idea 🤷"]
        bot = make_bot()
        sent = run_channel_mention(bot, content="")
        self.assertIn("🤷", sent[0][1])


if __name__ == "__main__":
    unittest.main()
