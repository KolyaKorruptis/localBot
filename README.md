# localBot: IRC Bot with local LLM Integration

> localBot is a fork of [AIRCBot](https://github.com/davidegat/AIRCBot) by
> [davidegat](https://github.com/davidegat), maintained independently since 2026.
> It is not affiliated with or endorsed by the original project.

This is a Python-based IRC bot that interacts with a local large language model, to provide conversational AI capabilities.

---
## New Features

Everything below is new in localBot and not present in upstream
[AIRCBot](https://github.com/davidegat/AIRCBot). 

### Channel Interaction
- **Replies to mentions in the channel.** When someone writes the bot's nick in
  a public message, the bot answers in the channel and addresses that person by
  nick. No OP/VOICE status and no authentication are required.
- **Whole-word nick matching**, case-insensitive, so a nick appearing inside a
  longer word or another nick does not trigger a reply.
- **Passive channel reading.** The bot keeps a rolling transcript of the last 50
  channel lines and feeds the most recent 15 to the LLM as background, so a
  reply follows what the channel was actually talking about.
- **Ignored users are neither answered nor recorded** in the transcript, and the
  bot never reacts to its own messages.

### Connection
- **SSL/TLS connections.** An **SSL** checkbox next to the port field encrypts
  the connection. It ticks itself when the port is `6697`, the conventional
  IRC-over-TLS port, and unticks if the port changes back - though clicking it
  yourself stops it following the port, so an explicit choice is never
  overwritten.
- **Certificates are verified** against the server hostname by default, with
  SNI. Servers using a self-signed certificate can be reached by setting
  `ssl_allow_self_signed` in `config.json` (see Configuration).

### Hardening
Channel input is treated as hostile. These limits exist so that one user cannot
pin the machine or stall the bot:

- **Every LLM request has a timeout.** Previously there was none, and because
  IRC events and generation shared a single thread, one hung request stopped
  the bot answering server PINGs until it was disconnected.
- **Generation runs off the IRC thread**, so the bot keeps talking to the
  server while the model works. Requests beyond `max_concurrent_generations`
  are **dropped rather than queued**, since a backlog only moves the stall.
- **Rate limits are keyed on the hostmask, not the nickname.** `/nick` is free,
  so anything keyed on a nickname is not a limit. There is a per-user cooldown
  and a global ceiling per minute.
- **A kill switch in the GUI.** The **AI Replies** checkbox stops all new
  generation immediately without disconnecting the bot from the channel.
- **Caps on prompt size, generated tokens, and reply length.** Context is
  bounded in characters as well as lines, because one user can pad a single
  line.
- **The bot only reads and answers in the channel it joined.**
- **Abuse is tracked against the hostmask, not the nickname.** The password
  lockout used to be keyed on the nickname, which made it decorative: `/nick`
  reset it, and 30 guesses in a row went through. Ignores follow the host too,
  so they survive a rename.
- **Password failures and blocked-output strikes are separate counters.**
  Sharing one meant the model's own wording could lock a user out of
  authenticating.
- **A blocked reply is charged to the user who prompted it, never to the
  recipient.** For a channel reply the recipient is the *channel*, so the old
  behaviour could put `#yourchannel` on the ignore list and silence the bot
  everywhere at once.
- **Every per-user map is size-bounded.** Nicknames are free to invent, so
  unbounded per-user state is memory a stranger can spend on your behalf.
- **Replies are clamped in bytes as well as characters,** because the IRC line
  limit is in bytes and accented text encodes longer than it looks.
- **Capability isolation.** The request carries messages and limits only, never
  `tools`/`functions`, the endpoint is never derived from user input, and model
  output is only ever sent as chat text. The bot cannot fetch a URL, read a
  file or load a model because it has no mechanism to, which is a stronger
  guarantee than filtering those phrases out of messages. `tests/test_security.py`
  fails if any of that changes.
- **Transcript entries cannot span lines.** The channel transcript is fed back
  to the model as context in `nick: message` form. IRC messages cannot contain
  newlines, but the bot's own replies are recorded there too and models do emit
  them, so a multi-line reply could otherwise plant a forged line attributed to
  another user. Lines are flattened before being recorded.
- **Channel context is fenced as untrusted data.** The transcript reaches the
  model inside a delimiter carrying a random nonce generated per request, and
  is explicitly labelled as data written by strangers rather than instructions.
  Because the nonce cannot be guessed, a user who writes a convincing closing
  marker stays inside the fenced region. The trusted instructions are placed
  *after* the block, so the last thing the model reads is yours, not theirs.
  This narrows prompt injection; it does not eliminate it - see below.
- **A tripwire for tool calls.** The bot never requests tools, so a compliant
  endpoint cannot return a tool call. If one arrives anyway, the reply is
  refused and reported loudly - it means the endpoint gained capabilities of
  its own. See *Locking down the LLM endpoint*.

### LLM Handling
- **Works with strict-role models.** Channel context is placed in the system
  prompt instead of the user turn, producing a valid alternating system/user
  request for models whose chat templates reject anything else (Gemma, for
  example).
- **The bot no longer echoes its own instructions.** The "answer briefly"
  guidance moved out of the user message and into the system prompt, so small
  models cannot repeat it back as part of a visible reply.
- **Null replies are handled.** If a request fails, the bot logs it instead of
  sending a literal `None` to the channel or user, and the empty answer is kept
  out of the conversation history where it would corrupt later requests.
- **API key authentication for the LLM endpoint.** localBot can send an
  OpenAI-style bearer token with every request, for an LM Studio server
  configured to require a key, or any OpenAI-compatible endpoint or reverse
  proxy in front of one. The key can come from the config or the
  `LOCALBOT_LLM_API_KEY` environment variable.
- **Authentication failures are reported.** A `401`/`403` is named as such in
  the console instead of looking like the model having nothing to say, and
  errors are always reported in the console - previously an LLM error was
  silent unless AI logging happened to be switched on.
- **More context per request.** Conversation history grew from 10 to 20
  messages and the per-request cap from 5 to 20, and the system prompt is now
  always retained when trimming, so the bot keeps its persona even with a busy
  channel.

### Removed
- **The RSS news feed is gone.** Upstream injected headlines from an external
  feed into every system prompt; localBot no longer fetches them, drops the
  `feedparser` dependency, and removes `feed_url` from `config.json`. Nothing
  leaves the machine now except the request to your local LLM.

- **AI-assisted conversation logging is gone.** Upstream summarised every three
  private messages through a second LLM call and appended the result to
  `user_logs/<nick>.log`. It replaced short, accurate lines with a model's
  paraphrase, doubled the work on the most expensive path by running inside the
  same generation slot as the reply, and quietly persisted other people's
  private messages. Removed along with `summary_prompt.txt`, the `log_dir` and
  `summary_prompt_file` settings, the *Enable AI Logging* checkbox and the
  *Open Log Folder* button. Conversations are now held in memory only.

### Project
- Renamed from AIRCBot to localBot; the script is now `localbot.py`.
- Added GPLv3 headers and fork attribution, which upstream did not carry.
- Added a `.gitignore` for Python, Firebase, editor, and log artifacts.

### Planned
_Nothing scheduled yet - planned work will be listed here._

---

## All Features

### General
- Connects to IRC servers and channels.
- Supports IRC commands and responses.
- Authenticates users for private interactions.
- Maintains a conversation history to provide contextually aware responses.
- Features a personal conversation history for each user.
- Replies in the channel whenever its nickname is mentioned, and can also be made to speak from the UI. Channel replies need no OP/VOICE status.

### AI-Powered Conversations
- Uses a locally hosted language model (via LMStudio API - download: https://lmstudio.ai/) to generate replies.
- Can be adapted to use remote API (like OpenAI - see comments in code for instructions).
- Natural, context-aware language generation prompt, adapted for IRC interactions.
- Also aware of: time, date, IRC server, channel, own nickname, user nickname.
- Brevity is requested in the system prompt rather than appended to the user's message, so models cannot echo the instruction back into a reply.

### Graphical Interface
- Provides a Tkinter-based GUI for managing the bot and monitoring its activity.
- Features connection setup, message and command sending, console logging.
- Includes a help menu for user guidance.
- Supports manual and automatic joining of channels.
- Displays IRC server console logs in real-time.

<img width="392" height="540" alt="localbot" src="https://github.com/user-attachments/assets/8d9bb3db-f131-4e15-94cf-393f7b1a79a7" />

### Security
- Requires password-based authentication for private messaging and for replies to `/me` actions.
- Channel replies are deliberately **not** authenticated, since anyone in the channel can mention the bot. They are bounded instead: rate limited per hostmask, capped in length, and stoppable from the UI.
- User will be de-authenticated upon: nick change, channel part, disconnection.
- Anti-brute-force blocking for failed logins, counted per hostmask so that changing nickname does not reset it.
- Uses a local LLM setup by default to increase privacy.
- Supports SSL/TLS connections, with certificate and hostname verification on by default.
- Inputs/Outputs sanitized to avoid LLM generating and sending raw commands if prompted to do so.
- Implements an ignore system for users attempting to trick the LLM into generating raw commands (ignore list resets when the program restarts). Ignores are keyed on the hostmask, and a channel can never be ignored.

### Command Management
- Supports sending and receiving IRC commands, with validation for potentially unsafe inputs.
- Command input field handles `/join`, `/kick`, `/quit`, `/whois` and `/op` (with short forms `/j`, `/k`, `/q`, `/w`, `/o`); anything else is passed to the server as a raw command.
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
Ensure the following libraries are installed and/or available:
- `tkinter`
- `requests`
- `threading`
- `time`
- `os`
- `subprocess`
- `json`
- `datetime`
- `hashlib`
- `irc` (irc.client) - **version 9.0 or newer**
- `ssl`, `functools` (standard library, used for TLS connections)

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
- **Nickname:** Bot's IRC nickname (e.g., `Egidio`).
- **Channel:** IRC channel to join (e.g., `#example`).
- **Password:** Password required for private messaging authentication. Connection will not be possible if no password is set.
- **Auto-Join:** Enable or disable automatic channel joining upon connection.
- **AI Replies:** Kill switch. Untick to stop all new AI generation immediately, without disconnecting from the channel.

### Customizing Configuration
Options like the system prompt, LLM endpoint, connection defaults and the abuse limits below are managed via the `config.json` file. Modify `config.json` to update these values without changing the code.

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

The key is never written to the console or to the AI logs; on connect the bot
only reports whether a key is in use and where it came from.

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

3. **Join a Channel:**
   "Auto-Join" checkbox will ensure the bot will join channel upon connection, uncheck to get control over it.
   After connecting, click "Join Channel" to enter the specified IRC channel if Auto-Join is disabled.

4. **Send Messages:**
   - Use the message input field to send messages to the default channel.
   - Use the command input field to send IRC commands (e.g., `/who`, `/mode`).

5. **Private Messaging:**
   - Users can send direct messages to the bot.
   - The bot will request authentication if the user is not pre-authorized.
   - Once authenticated, users can interact with the bot's AI brain and get responses.
   - Users will be de-authenticated upon: nick change, channel part, disconnection.

6. **Notes on LMStudio**
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
> entry, and followed by the real instructions - but no prompt-level defence is
> absolute. A sufficiently persuasive message can still steer a reply's tone or
> content. Treat the bot's channel output as untrusted itself, and never wire
> it to anything that acts.

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

