# localBot: IRC Bot with local LLM Integration

> localBot is a fork of [AIRCBot](https://github.com/davidegat/AIRCBot) by
> [davidegat](https://github.com/davidegat), maintained independently since 2026.
> It is not affiliated with or endorsed by the original project.

This is a Python-based IRC bot that interacts with a local large language model, to provide conversational AI capabilities.

---

## Contents

- [What's Different from AIRCBot](#whats-different-from-aircbot)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Locking Down the LLM Endpoint](#locking-down-the-llm-endpoint)
- [Running the Tests](#running-the-tests)
- [License](#license)

---
## What's Different from AIRCBot

**Conversation**
- **Replies to mentions in the channel.** Say the bot's nick and it answers,
  addressing you by name. 
- **It reads the channel passively,** so a reply follows what people were
  actually talking about rather than answering in a vacuum.
- **Random remarks instead of silence.** When a generation fails the bot can
  answer with a canned one-liner from `remarks.txt` rather than saying nothing.

**Connection**
- **SSL/TLS** with certificate and hostname
  verification. See [Configuration](#connection-parameters).
- **API key authentication** for the LLM endpoint

**Not being a liability in a public channel**
- **Nothing can pin the machine.** Requests have timeouts, generation runs off
  the IRC thread, and there is a kill switch in the GUI now. Upstream had none of
  this: a single slow request stopped the bot answering server PINGs until it
  was disconnected.
- **Limits are keyed to the hostmask, not the nickname,** so a nick change no longer
  resets them. Previously the password lockout was just decorative - 30 guesses in a
  row went through.
- **Channel text is treated as hostile input.** It reaches the model fenced and
  labelled as data, never mixed with the bot's own output. Measured against a
  live model.
- **The bot cannot act.** It sends no tools and executes nothing, so it cannot
  be talked into fetching a URL or reading a file - and it says so loudly if
  the endpoint ever returns a tool call. See
  [Locking Down the LLM Endpoint](#locking-down-the-llm-endpoint).

### Removed
- **AI-assisted conversation logging.** A second LLM call paraphrased private
  user messages and wrote them to `user_logs/<nick>.log`. The result was worse
  than the lines it replaced, twice the work on the slowest path, and a quiet
  record of other people's private conversations with the bot. 

- **The channel message input.** It sent whatever the operator typed to the
  channel as the bot, indistinguishable from a generated reply. This impersonation
  broke the rule that the bot only speaks when addressed by its nickname. 

- **The RSS news feed.** Upstream put headlines from an external rss-feed into every
  system prompt using up tokens, `feedparser` is no longer a dependency.

- **The `/kick` and `/op` shortcuts.** This is not a moderation bot. The raw command
  passthrough still exists.

- **The in-app help window and `help_text.txt`.** They restated this README and
  drifted out of sync.

### Project
- Renamed from AIRCBot to localBot; the script is now `localbot.py`.
- Added GPLv3 headers and fork attribution, which upstream did not carry.
- Added a test suite, `tests/test_security.py`.
- Added a `.gitignore` for Python, Firebase, editor, and log artifacts.

---

## Features

### General
- Connects to IRC servers and channels, plain text or over SSL/TLS.
- Joins one channel, manually or automatically on connect.
- Authenticates users for private interactions, with a personal conversation
  history for each.
- Replies in the channel whenever its nickname is mentioned. No OP/VOICE status
  or authorization is required.

### Conversation
- Uses a locally hosted language model (via the LMStudio API) to generate replies,
  or any OpenAI-compatible endpoint.
- Keeps a rolling transcript of the last 50 channel lines and feeds the most
  recent 15 to the model as background.
- Matches its nickname as a whole word, case-insensitively, so a nick inside a
  longer word does not trigger a reply.
- Aware of: time, date, IRC server, channel, own nickname, user nickname.
- The entire prompt lives in `system_prompt.txt`; nothing is appended in code.
- Handles empty replies rather than sending a literal `None`, and reports
  request failures in the console instead of failing silently.
- Optionally answers a failed generation with a random line from
  [`remarks.txt`](#random-remarks) instead of staying silent.

### Graphical Interface
- Tkinter GUI for connection setup, IRC commands and console logging.
- **SSL** checkbox beside the port field, auto-checked on port `6697`.
- **AI Replies** kill switch: stops all new generation without disconnecting.
- Displays IRC server console logs in real time.

### Security
- Password authentication for private messages and `/me` actions, with
  de-authentication on nick change, channel part or disconnection.
- Channel replies are deliberately **not** authenticated but and are bounded
  instead: rate limited, capped in length, and stoppable from the UI.
- Abuse tracking is keyed on the hostmask, so changing nickname does not reset
  a lockout or an ignore. Password failures and blocked-output strikes are
  counted separately, and the channel can never be ignored.
- Output passes an allowlist, so the model can never emit raw IRC commands,
  newlines or a line over the protocol limit.
- Every per-user map is size-bounded, so nobody can grow the bot's memory by
  inventing nicknames.
- SSL/TLS certificates are verified by default; [`ssl_allow_self_signed`](#ssl_allow_self_signed) relaxes that.
- The bot only reads and answers in the channel it joined.

### Resource Limits
Every limit is tunable in `config.json`; see
[Abuse and resource limits](#abuse-and-resource-limits).
- Requests time out; generation runs on a worker thread so a slow model never
  stalls the IRC connection.
- Generations beyond the concurrency cap are dropped rather than queued.
- Per-hostmask cooldown plus a global ceiling per minute.
- Caps on generated tokens, prompt size, and reply length in both characters
  and UTF-8 bytes.

### Command Management
- Command input field handles `/msg`, `/topic`, `/whois` (`/w`) and `/quit`
  (`/q`). Anything else is passed to the server as a raw command, so any
  standard verb works if you write the full syntax.
- `/join` (`/j`) is refused: use the **Join Channel** button or Auto-Join, so
  the bot only ever occupies the one channel it was configured for.
- Automated responses to common channel interactions like receiving OP/VOICE.
- Command logs are displayed in the GUI for transparency.

---

## Requirements

### System Requirements
- Python 3.9 or later (developed on 3.12).
- [LM Studio](https://lmstudio.ai/) or any OpenAI-compatible endpoint, reachable
  at `llm_endpoint` (default `http://localhost:1234/v1/chat/completions`).
- An internet connection for IRC. The model runs locally, so nothing but IRC
  traffic leaves the machine.

A remote API such as OpenAI works too - see the comments in `localbot.py` - at
the cost of privacy, and of paying per request.

### Python Libraries
Only three dependencies are not part of the standard library:
- `tkinter` - the GUI (packaged separately by most distributions)
- `requests` - HTTP calls to the LLM endpoint
- `irc` (irc.client) - **version 9.0 or newer**

Install missing dependencies using (example):
```bash
pip install requests irc
```

> **Note on the `irc` package:** localBot needs `irc.client.Reactor`, which
> exists only in `irc` 9.0 and newer. Distribution packages can be much older -
> Ubuntu 24.04's `python3-irc` is 8.5.3 and will fail with
> `AttributeError: module 'irc.client' has no attribute 'Reactor'`. Install a
> current version from PyPI instead. `tkinter` is the exception: it is not on
> PyPI, so install it from your distribution (`sudo apt install python3-tk` on
> Debian/Ubuntu). If you use a virtual environment, create it with
> `--system-site-packages` so it can see `tkinter`.

---

## Installation

1. **Clone the Repository:**
   Download the source code from the repository:
   ```bash
   git clone https://github.com/KolyaKorruptis/localBot.git
   cd localBot
   ```

2. **Run the Script:**
   Execute the Python script using:
   ```bash
   python localbot.py
   ```
3. **LLM (LMStudio)**
   Make sure your local LLM is up and running before connecting to the IRC server, or you will only get a zombie bot parked on a channel.

---

## Configuration

### Connection Parameters
In the graphical interface, fill in the following fields:
- **Server:** IRC server address (e.g., `open.ircnet.net`).
- **Port:** IRC server port (default: `6667`; use `6697` for SSL).
- **SSL:** Encrypt the connection with TLS. Ticks itself when the port is `6697`; tick or untick it by hand to override, and it will then stop following the port.
- **Nick:** Bot's IRC nickname (e.g., `Bathsheba`).
- **Channel:** IRC channel to join (e.g., `#example`). A missing `#` is added for you, so `example` works too.
- **Password:** Password required for private messaging authentication. Connection will not be possible if no password is set.
- **Auto-Join:** Enable or disable automatic channel joining upon connection.
- **AI Replies:** Kill switch. Untick to stop all new AI generation immediately, without disconnecting from the channel.

### Customizing Configuration
The LLM endpoint, connection defaults and the abuse limits below are managed via the `config.json` file.

`system_prompt.txt` is read from a fixed path beside `localbot.py` and is
deliberately **not** configurable. A missing or blank `system_prompt.txt` 
now refuses to start.

#### `llm_api_key`
Empty by default, meaning no authentication. Set it to send an `Authorization: Bearer <key>` header with every LLM request:

```json
"llm_api_key": "your-key-here"
```

**Prefer the environment variable.** `config.json` is tracked by git, so a key
written there is easy to commit by accident. `LOCALBOT_LLM_API_KEY` takes
precedence over `config.json` when both are set:

```bash
export LOCALBOT_LLM_API_KEY="your-key-here"
python localbot.py
```

The key is never written to the console; on connect the bot reports only that a
key is in use and which source it came from.

#### Random remarks
`remarks.txt` holds one remark per line. Blank lines are ignored and lines
starting with `#` are comments, so the file ships inert - add lines to switch
the feature on.

The bot sends one when a generation produces **nothing**: a request error, a
timeout, an empty reply, or a refused tool call. It stays silent when it
declines on purpose - rate limited, over the concurrency cap, or **AI Replies**
switched off - because those exist to stop it talking.

A remark may use `{speaker_nickname}`, `{bot_nickname}` and `{channel}`.
Substitution is a plain text replacement, not `str.format`, so a joke
containing braces of its own is safe and a mistyped placeholder shows up in the
reply instead of raising on the very path that handles a failure. A remark
containing `{speaker_nickname}` is sent *without* the usual `nick: ` prefix, so
the name is not said twice.

Remarks are yours, not generated, so they bypass the output allowlist and the
raw-command filter. Emoji survive, and a remark may open with a word like
`TIME` without tripping the filter or charging anyone an abuse strike. They are
still flattened to one line and clamped to the IRC line limit.

> There is no cooldown: one remark per failed generation. If the endpoint goes
> down, every mention gets an answer - amusing once, noise by the tenth. The
> **AI Replies** checkbox silences it, and the console still shows the real
> error.

#### Abuse and resource limits
All tunable in `config.json`. The defaults are deliberately conservative:

| Key | Default | What it bounds |
| --- | --- | --- |
| `llm_connect_timeout_seconds` | `10` | Waiting for the endpoint to accept a connection |
| `llm_timeout_seconds` | `60` | Waiting for a generation before giving up |
| `llm_max_tokens` | `300` | Generated tokens - the most direct cap on model time |
| `max_reply_length` | `400` | Characters put on the wire |
| `max_reply_bytes` | `400` | UTF-8 bytes on the wire - the real IRC line limit |
| `max_context_chars` | `2000` | Channel context assembled into a prompt |
| `max_line_chars` | `300` | A single recorded channel line |
| `reply_cooldown_seconds` | `10` | Seconds between generations for one hostmask |
| `replies_per_minute` | `8` | Generations per rolling minute, everyone combined |
| `max_concurrent_generations` | `1` | Generations in flight; extras are dropped |
| `max_tracked_users` | `500` | Entries kept in each per-user map before the oldest are dropped |
| `auth_failure_limit` | `3` | Wrong passwords from one host before a lockout |
| `auth_block_seconds` | `900` | How long that lockout lasts |
| `abuse_strike_limit` | `5` | Blocked replies charged to one host before it is ignored |

#### `ssl_allow_self_signed`
Off (`false`) by default. When SSL is enabled, localBot verifies the server's
certificate chain and checks it matches the hostname you connected to. Some
smaller IRC networks use self-signed certificates, which are rejected by that
check. Setting this to `true` lets the bot connect to them anyway:

```json
"ssl_allow_self_signed": true
```

> **This disables certificate verification entirely.** The connection is
> still encrypted, but it no longer proves who is on the other end.
> Only enable it for a server whose certificate you already trust.
> localBot logs a warning in the console whenever it connects with verification
> disabled.

---

## Usage

Start your local LLM, then run `python localbot.py`.

1. **Connect.** Fill in the [connection fields](#connection-parameters) - a
   password is mandatory - and click **Connect**. With **Auto-Join** ticked the
   bot joins on connect; otherwise click **Join Channel**.
2. **Talk to it.** Mention its nickname in the channel, or send it a private
   message and answer the authentication question with the password you set.
3. **Send IRC commands.** Use the command field, for example
   `/msg NickServ REGISTER ...` to register the bot's nickname. 

**Model settings:** tested at temperature 0.55-0.65, response length 100-150,
context 2000 tokens.

---

## Locking Down the LLM Endpoint

In the OpenAI protocol, tool use is driven by the client: the caller sends a
`tools` array, the model may answer with `tool_calls`, and **the caller executes
them**. localBot sends no tools and executes nothing, so on that protocol alone
it cannot be talked into fetching a URL or reading a file.

**LM Studio goes further than the protocol, so do not rely on that alone.** Its
server can run MCP tools itself, governed by two permissions:

| Permission | UI toggle | Effect when allowed |
| --- | --- | --- |
| `dynamicRemoteMcpServer` | *Allow Remote MCP* | An API client may name remote MCP servers **per request**; LM Studio connects and runs them for the duration of that request |
| `pluginUse` | *Allow calling servers from mcp.json* | An API client may invoke the MCP servers configured in `mcp.json` |

Both default to `deny`, and LM Studio forces `pluginUse` back to `deny` unless
token authentication is set to *required*. Check them - the state lives in
`.lmstudio/.internal/permissions-store.json`, at server level and again per
token:

```json
"serverPermissions": { "dynamicRemoteMcpServer": "deny", "pluginUse": "deny" }
```

Keep both on `deny` unless you have a specific reason not to. Per-token
permissions are the tighter control: a token may deny what the server allows.

localBot never sends `tools`, never executes anything, and reads only the reply
text, so it cannot be talked into fetching a URL or reading a file. But that is a
property of the bot. Guaranteeing what LM Studio itself can reach needs controls
on that machine:

- **Turn off network access for the LM Studio process.** This is the single
  strongest control: a URL fetcher or a network-backed MCP server cannot work
  without egress, whatever the configuration says. The bot connects *inbound* to
  LM Studio, so blocking outbound traffic does not affect it.
- **Check LM Studio's MCP configuration** (`mcp.json`, editable from inside the
  app) and remove any servers you did not add deliberately. `mcp.json` alone is
  not the whole story: confirm the two server permissions above are `deny`.
- **Turn off *Redact Content* logging.** LM Studio writes prompts and responses
  to `server-logs/` by default (`logSensitiveData`), which for this bot means
  every channel message and private conversation lands on disk in plaintext.
  The toggle is on the Developer page behind the **"..." (More options)** button
  next to the server log panel, not in the main settings list, and it is
  inverted: switching *Redact Content* **on** sets `logSensitiveData` to false.
- **Keep the server on loopback.** Leave "serve on local network" off so nothing
  but the bot can reach it.
- **Set an API key** (see `llm_api_key`) so that even on loopback, only the bot
  can drive the endpoint. This matters more than it first appears: LM Studio
  serves `POST /api/v1/models/load` and `POST /api/v1/models/download` on the
  *same port* as chat completions, so the key the bot uses also authorises
  loading and downloading models. Keep it in the environment variable, never in
  the tracked `config.json`.
- **Run LM Studio as a user that cannot read anything you care about**, or in a
  container or VM. Retrieval can only reach files the process can open, and this
  is what turns that from a habit into a guarantee.

None of this is enforceable from the bot, which is why the tripwire exists: if
LM Studio ever does return a tool call, you will see `LLM - REFUSED` in the
console.

> Capability isolation limits the blast radius; it does not stop prompt
> injection. A channel user can still influence the *wording* of a reply. What
> they cannot do is cause an action, because no mechanism to act exists.
>
> The fencing described above raises the cost of injection - untrusted text is
> labelled, delimited with an unguessable nonce, confined to one line per
> entry, followed by the real instructions, and never mixed with the bot's own
> output - but no prompt-level defence is absolute. A sufficiently persuasive
> message can still steer a reply's tone or content, and a user can always steer
> their *own* reply simply by asking.

---

## Running the Tests

```bash
python -m unittest discover -s tests -v
```

`tests/test_security.py` holds 55 tests covering the guarantees that are easy to
break without noticing:

| Area | What it pins down |
| --- | --- |
| Capability isolation | No `tools`/`functions` in the payload, an endpoint never derived from user input, a timeout always present |
| Tool-call tripwire | A returned tool call is refused and reported, while the empty `tool_calls: []` a real server sends on every reply is not mistaken for one |
| Untrusted framing | Channel text is fenced with a per-request nonce, a forged closing marker stays inside the fence, and the operator's words come last |
| Self-contamination | The bot's own replies never re-enter its channel context |
| Rate limiting | Cooldowns and the global ceiling key on the hostmask, so changing nickname does not reset them |
| Concurrency | Excess generations are dropped rather than queued, and a failed one releases its slot |
| Bounds | Reply length in characters and UTF-8 bytes, prompt size, and a cap on every per-user map |
| Prompt loading | A missing or blank `system_prompt.txt` stops the bot instead of running it untuned |

Run it after touching anything in the message-handling path. Several of these
exist because the behaviour they describe was measured against a live model and
turned out to differ from what seemed obvious.

---

## License

localBot is free software, licensed under the **GNU General Public License,
version 3**. See the [LICENSE](LICENSE) file for the full text.

localBot is a modified version of AIRCBot, originally written by
[davidegat](https://github.com/davidegat) and released under the same license.
Copyright of the original work remains with its author; changes made in this
fork are Copyright (C) 2026 KolyaKorruptis. A summary of those changes is in
the header of `localbot.py`, and the full record is in this repository's commit
history.

This program comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

