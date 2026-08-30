# localBot: IRC Bot with local LLM Integration

> localBot is a fork of [AIRCBot](https://github.com/davidegat/AIRCBot) by
> [davidegat](https://github.com/davidegat), maintained independently since 2026.
> It is not affiliated with or endorsed by the original project.

This is a Python-based IRC bot that interacts with a local large language model, to provide conversational AI capabilities. The bot is able of joining an IRC channel, responding to direct messages, fetching the latest news, and managing authenticated user interactions. This document outlines how to install, configure, and use localBot effectively with LMStudio (https://lmstudio.ai/) locally.

You can easily modify this software to use external APIs if needed (instructions in code comments).

---

## Features

### General
- Connects to IRC servers and channels.
- Supports IRC commands and responses.
- Authenticates users for private interactions.
- Maintains a conversation history to provide contextually aware responses.
- Features a personal conversation history for each user.
- Limited interaction with channel (if asked by user via UI, or if OP/VOICE status is given).

### AI-Powered Conversations
- Uses a locally hosted language model (via LMStudio API - download: https://lmstudio.ai/) to generate replies.
- Can be adapted to use remote API (like OpenAI - see comments in code for instructions).
- Natural, context-aware language generation prompt, adapted for IRC interactions.
- Fetches and references the latest news for conversations about current events.
- Also aware of: time, date, IRC server, own nickname, user nickname.
- Messages sent to the LLM include a "(please answer briefly)" suffix to ensure concise responses.

### Graphical Interface
- Provides a Tkinter-based GUI for managing the bot and monitoring its activity.
- Features connection setup, message and command sending, console logging.
- Includes a help menu for user guidance.
- Supports manual and automatic joining of channels.
- Displays IRC server console logs in real-time.

![image](https://github.com/user-attachments/assets/384b1112-b769-4e05-92d0-8d642bfd3d80)
![image](https://github.com/user-attachments/assets/19530dc6-fd81-4e5f-b6f3-726a2fc4b0b2)

### Security
- Requires password-based authentication for private messaging.
- User will be de-authenticated upon: nick change, channel part, disconnection.
- Implements basic anti-brute-force measures with temporary blocking for failed login attempts.
- Uses a local LLM setup by default to increase privacy. 
- Secure connection is supported by Python IRC libraries.
- Inputs/Outputs sanitized to avoid LLM generating and sending raw commands if prompted to do so.
- Implements an ignore system for users attempting to trick the LLM into generating raw commands (ignore list resets when the program restarts).

![image](https://github.com/user-attachments/assets/f21ea601-8cc8-4a9f-8d90-7084c0271f87)

### Logging Features
- The bot logs summaries of conversations for authenticated users in the `user_logs` directory.
- Logs are generated with AI assistance, summarizing the last three user messages in a concise paragraph.
- Logging must be enabled in the interface before connecting to the IRC server.
- Each user's conversation history is saved in a separate file for easier review.

### Command Management
- Supports sending and receiving IRC commands, with validation for potentially unsafe inputs.
- Command input field allows sending IRC-specific commands, such as `/whois`, `/msg`, `/kick`, and others.
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
- `feedparser`
- `threading`
- `time`
- `os`
- `subprocess`
- `json`
- `datetime`
- `hashlib`
- `irc` (irc.client)

If you plan to change the code to use external APIs, consider importing `openai`. Please refer to OpenAI documentation for API access, and code comments for instructions.

Install missing dependencies using (example):
```bash
pip install requests feedparser
```

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
- **Port:** IRC server port (default: `6667`).
- **Nickname:** Bot's IRC nickname (e.g., `Egidio`).
- **Channel:** IRC channel to join (e.g., `#example`).
- **Password:** Password required for private messaging authentication. Connection will not be possible if no password is set.
- **Auto-Join:** Enable or disable automatic channel joining upon connection.
- **Enable AI Logging:** Option to log AI-assisted summaries of user interactions.

### Customizing Configuration
Options like the system prompt, summary prompt, logging directory, LLM endpoint, and other defaults are now managed via the `config.json` file. Modify `config.json` to update these values without changing the code.

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

6. **News Integration:**
   - The bot fetches the latest 3 news headlines and includes them in responses when/if relevant or if asked to.
   - You can customize the RSS feed in `config.json`.

7. **AI-Assisted Summaries:**
   - If logging is enabled, the bot will summarize user interactions every three messages.
   - Summaries are concise and saved to the `user_logs` directory under the user's nickname.

8. **Notes on LMStudio**
   - Tested with: Temp 0.55-0.65 / Response Length 100-150 / Context 2000 tokens
   - Similar results with different models, pick your favorite.
   - Download https://lmstudio.ai/

---

## Other Security Notes or Issues

- Multiple messages sent to the bot are queued. This must be handled in the future to avoid overloads 'cause there's so many people on IRC servers nowadays (of course, I'm ironic).
- Do not leave your bot unattended or in the background to avoid abuse by users or breaking server ToS.
- Removing password protection from code seems not a good idea, but you decide.
- Conversation history is different for each user; anyways, do not disclose personal information if using external APIs like OpenAI.
- The bot is not multiuser in a true sense. Only one password is allowed to be set. Choose a **new one** before sharing it with other users. Do not reuse your own passwords, please.
  
---

## Other Limitations

Some features are not supported to avoid complexity, or for security reasons:
- Supports only one channel at a time to avoid excessive exposure.
- Supports ACTIONS but not the full CTCP protocol (Client-To-Client Protocol).
- Does not handle DCC (Direct Client-to-Client) connections at all.
- Requires local hosting of the LMStudio model to increase privacy but can be modified to use an external API (see examples in code comments).

---

## Troubleshooting

1. **Connection Issues:**
   - Ensure server and port are correct.
   - Check your internet connection.
   - Check your firewall and/or VPN.
   - Using TOR? Enter a .onion server; regular servers may have you banned.

2. **Authentication Fails:**
   - Verify the correct password is entered.
   - Wait if temporarily blocked.
   - Hope if ignored for the session.
   - Restart the bot to reset blocks and ignores if you are the master.

3. **AI Response Errors:**
   - Ensure LMStudio is running and accessible at `http://localhost:1234/v1/chat/completions`. A warning should be issued in the bot console if the local API is unreachable.
      - NOTE: To use a different endpoint for local LLMs, update the value in `config.json`.
   - If you modified the code to support an external API, check if your endpoint and parameters are correct for your model.
   - If you modified the system prompt, try adapting it to get better answers.

4. **Strange(r) Things**
   - Reply quality and length depend upon which model you are using and relative settings, not on this program.
   - The included prompt is generally okay; you may want to change it to experiment with different results.
   - Also, try using different models and settings for different results.
   - Keep values low on your LLM (or parameters in `config.json` if using an external API): short response (100-150 tokens), short context (2000-3000), not too much temperature (0.55-0.65).

---

## License

localBot is free software, licensed under the **GNU General Public License,
version 3**. See the [LICENSE](LICENSE) file for the full text.

localBot is a modified version of AIRCBot, originally written by
[davidegat](https://github.com/davidegat) and released under the same license.
Copyright of the original work remains with its author; changes made in this
fork are Copyright (C) 2026 Nicolai Sandow. A summary of those changes is in
the header of `localbot.py`, and the full record is in this repository's commit
history.

This program comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

---

## Acknowledgments

- Built using Python and Tkinter.
- AI responses by LMStudio.
- Powered by Linux and coffee.
- Cats. I love cats. And coffee.
- @lastknight (https://github.com/lastknight) who indirectly inspired it during a Christmas Night live of "Ciao Internet" :)
---

For questions, contributions, or feature requests, feel free to contact the project maintainer or open an issue in the repository. Software is provided as-is. By using it, you accept to take all responsibility for any damage of any kind this software may cause to your data, device(s), firm, corporation, shop, family, friends, whole life, belongings, backyard, dignity, and other moral and psychological stuff, your body or your cats'.
