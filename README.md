# localBot: IRC Bot with local LLM Integration

> localBot is a fork of [AIRCBot](https://github.com/davidegat/AIRCBot) by
> [davidegat](https://github.com/davidegat), maintained independently since 2026.
> It is not affiliated with or endorsed by the original project.

This is a Python-based IRC bot that interacts with a local large language model, to provide conversational AI capabilities.

---
## What's Different from AIRCBot

The changes worth knowing about. Everything is documented in full further down.

**Conversation**
- **Replies to mentions in the channel.** Say the bot's nick and it answers,
  addressing you by name. No OP/VOICE status, no authentication.
- **It reads the channel passively,** so a reply follows what people were
  actually talking about rather than answering in a vacuum.
- **It does not pretend to be human.** Upstream's prompt told it to hide its
  nature; ask localBot what it is and it tells you.

**Connection**
- **SSL/TLS, on by default for port 6697,** with certificate and hostname
  verification. See [Configuration](#connection-parameters).
- **API key authentication** for the LLM endpoint, from the environment rather
  than a tracked file.

**Not being a liability in a public channel**
- **Nothing can pin the machine.** Requests have timeouts, generation runs off
  the IRC thread, and there is a kill switch in the GUI. Upstream had none of
  this: a single slow request stopped the bot answering server PINGs until it
  was disconnected.
- **Limits are keyed to the hostmask, not the nickname,** so `/nick` no longer
  resets them. The password lockout was previously decorative - 30 guesses in a
  row went through.
- **Channel text is treated as hostile input.** It reaches the model fenced and
  labelled as data, never mixed with the bot's own output. Measured against a
  live model, an injected instruction was obeyed 4 times out of 6 before this
  and 0 times out of 6 after.
- **The bot cannot act.** It sends no tools and executes nothing, so it cannot
  be talked into fetching a URL or reading a file - and it says so loudly if
  the endpoint ever returns a tool call. See
  [Locking Down the LLM Endpoint](#locking-down-the-llm-endpoint).

### Removed
- **The RSS news feed.** Upstream put headlines from an external feed into every
  system prompt. Nothing leaves the machine now except the request to your local
  LLM, and `feedparser` is no longer a dependency.

- **AI-assisted conversation logging.** A second LLM call paraphrased every three
  private messages into `user_logs/<nick>.log`: worse than the lines it replaced,
  twice the work on the slowest path, and a quiet record of other people's
  private conversations. Held in memory only now.

- **The channel message input.** It sent whatever the operator typed to the
  channel as the bot, indistinguishable from a generated reply. Say things in
  the channel as yourself.

- **The `/kick` and `/op` shortcuts.** A conversational bot, not a moderation
  one. Neither verb is blocked - both still work through the raw command
  passthrough - the convenience is simply not offered.

- **The in-app help window and `help_text.txt`.** They restated this README and
  drifted out of date.

### Project
- Renamed from AIRCBot to localBot; the script is now `localbot.py`.
- Added GPLv3 headers and fork attribution, which upstream did not carry.
- Added a test suite, `tests/test_security.py`.
- Added a `.gitignore` for Python, Firebase, editor, and log artifacts.

### Planned
_Nothing scheduled yet - planned work will be listed here._

---

## Features

### General
- Connects to IRC servers and channels, plain or over SSL/TLS.
- Joins one channel, manually or automatically on connect.
- Authenticates users for private interactions, with a personal conversation
  history for each.
- Replies in the channel whenever its nickname is mentioned. No OP/VOICE status
  is required, and there is no way to make it speak otherwise.

### Conversation
- Uses a locally hosted language model (via the LMStudio API - download:
  https://lmstudio.ai/) to generate replies, or any OpenAI-compatible endpoint.
- Keeps a rolling transcript of the last 50 channel lines and feeds the most
  recent 15 to the model as background.
- Matches its nickname as a whole word, case-insensitively, so a nick inside a
  longer word does not trigger a reply.
- Aware of: time, date, IRC server, channel, own nickname, user nickname.
- The entire prompt lives in `system_prompt.txt`; nothing is appended in code.
- Handles empty replies rather than sending a literal `None`, and reports
  request failures in the console instead of failing silently.

### Graphical Interface
- Tkinter GUI for connection setup, IRC commands and console logging.
- **SSL** checkbox beside the port field.
- **AI Replies** kill switch: stops all new generation without disconnecting.
- Displays IRC server console logs in real time.

### Security
- Password authentication for private messages and `/me` actions, with
  de-authentication on nick change, channel part or disconnection.
- Channel replies are deliberately **not** authenticated - anyone in the
  channel can mention the bot - and are bounded instead: rate limited, capped
  in length, and stoppable from the UI.
- Abuse tracking is keyed on the hostmask, so changing nickname does not reset
  a lockout or an ignore. Password failures and blocked-output strikes are
  counted separately, and a channel can never be ignored.
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
- `/kick` and `/op` have no shortcuts (see *Removed*).
- Automated responses to common channel interactions like receiving OP/VOICE.
- Command logs are displayed in the GUI for transparency.

---

## Requirements

### System Requirements
- Tested on Python 3.9 or later.
- Internet connection.
- LMStudio (https://lmstudio.ai/) or equivalent local language model API.
- Bot is configured to use LMStudio API at `http://localhost:1234/v1/chat/completions` endpoint (can be changed via `config.json` file).
- If you can't run a local LLM model, follow instructions in code comments to use your own external API endpoint (like OpenAI API - Please refer to OpenAI documentation for API access). Less privacy is to be expected in this use case. Beware external APIs can charge you money at each request!

### Python Libraries
Only three dependencies are not part of the standard library:
- `tkinter` - the GUI (packaged separately by most distributions)
- `requests` - HTTP calls to the LLM endpoint
- `irc` (irc.client) - **version 9.0 or newer**

If you plan to change the code to use external APIs, consider importing `openai`. Please refer to OpenAI documentation for API access, and code comments for instructions.

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
- **Nick:** Bot's IRC nickname (e.g., `Egidio`).
- **Channel:** IRC channel to join (e.g., `#example`).
- **Password:** Password required for private messaging authentication. Connection will not be possible if no password is set.
- **Auto-Join:** Enable or disable automatic channel joining upon connection.
- **AI Replies:** Kill switch. Untick to stop all new AI generation immediately, without disconnecting from the channel.

### Customizing Configuration
The LLM endpoint, connection defaults and the abuse limits below are managed via the `config.json` file.

`system_prompt.txt` is read from a fixed path beside `localbot.py` and is
deliberately **not** configurable. Pointing at it from `config.json` only
created a way to mistype the path: a missing file used to load as an empty
string, so one typo left the bot running with no persona, no brevity rule and
no honesty clause, and nothing reported it. A missing or blank
`system_prompt.txt` now refuses to start.

This README is the only documentation; there is no in-app help window (see
*Removed*).

#### `llm_api_key`
Empty by default, meaning no authentication. Set it to send an
`Authorization: Bearer <key>` header with every LLM request:

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

Setting `llm_timeout_seconds` to a very large value re-creates the original
problem, where a stuck endpoint takes the bot down with it.

#### `ssl_allow_self_signed`
Off (`false`) by default. When SSL is enabled, localBot verifies the server's
certificate chain and checks it matches the hostname you connected to. Some
smaller IRC networks use self-signed certificates, which are rejected by that
check. Setting this to `true` lets the bot connect to them anyway:

```json
"ssl_allow_self_signed": true
```

> **This disables certificate verification entirely - both the chain and the
> hostname check - not just for self-signed certificates.** The connection is
> still encrypted, but it no longer proves who is on the other end, so it can be
> intercepted by anyone able to redirect your traffic. Only enable it for a
> server whose certificate you already trust. localBot logs a warning in the
> console whenever it connects with verification disabled.

---

## Usage

Make sure your local LLM is up and running, then:

1. **Connect the Bot:**
   Set your parameters. Please note that bot password is mandatory.
   Click the "Connect" button.

2. **Join a Channel:**
   "Auto-Join" checkbox will ensure the bot will join channel upon connection, uncheck to get control over it.
   After connecting, click "Join Channel" to enter the specified IRC channel if Auto-Join is disabled.

3. **Send IRC Commands:**
   - Use the command input field for IRC commands, for example `/msg NickServ REGISTER ...` to register the bot's nickname.
   - There is deliberately no field for sending chat messages to the channel: an operator line would be indistinguishable from a generated reply. See *Removed*.

4. **Private Messaging:**
   - Users can send direct messages to the bot.
   - The bot will request authentication if the user is not pre-authorized.
   - Once authenticated, users can interact with the bot's AI brain and get responses.
   - Users will be de-authenticated upon: nick change, channel part, disconnection.

5. **Notes on LMStudio**
   - Tested with: Temp 0.55-0.65 / Response Length 100-150 / Context 2000 tokens
   - Similar results with different models, pick your favorite.
   - Download https://lmstudio.ai/

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
console instead of a silent empty reply.

> Capability isolation limits the blast radius; it does not stop prompt
> injection. A channel user can still influence the *wording* of a reply. What
> they cannot do is cause an action, because no mechanism to act exists.
>
> The fencing described above raises the cost of injection - untrusted text is
> labelled, delimited with an unguessable nonce, confined to one line per
> entry, followed by the real instructions, and never mixed with the bot's own
> output - but no prompt-level defence is absolute. A sufficiently persuasive
> message can still steer a reply's tone or content, and a user can always steer
> their *own* reply simply by asking, as they could ask for one in French. Treat
> the bot's channel output as untrusted itself, and never wire it to anything
> that acts.

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

