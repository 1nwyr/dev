# Sol's RNG Developer Watch Bot

Sol's RNG Developer Watch Bot is a Discord bot that monitors Sol's RNG game servers for developer and owner activity. It polls the Roblox presence API, tracks biome "found" messages in specific channels, and posts live status embeds so your moderation team can react quickly to sightings.

## Features
- **Developer and owner detection** – Polls the Roblox presence API to detect developers and owners entering Sol's RNG and announces sightings with role pings. 【main.py†L128-L199】【main.py†L238-L290】
- **Badge verification hooks** – Includes helper functions for checking Roblox badges that can be extended for dimensional badge detection. 【main.py†L104-L127】
- **Biome find tracking** – Monitors configured Discord channels for the keyword `found` and increments a running counter. 【main.py†L292-L325】
- **Automated status updates** – Posts and maintains an embed summarizing uptime, ping, biome finds, and API errors. 【main.py†L214-L276】
- **Slash command support** – Provides a `/status` command for on-demand status information. 【main.py†L340-L365】
- **Resilient logging** – Streams logs to both the console and `bot.log`, with UTF-8 support for Windows terminals. 【main.py†L5-L44】

## Requirements
- Python 3.10+
- [discord.py](https://discordpy.readthedocs.io/en/stable/) (2.x)
- [aiohttp](https://docs.aiohttp.org/)

Install the dependencies into your virtual environment:

```bash
python -m pip install discord.py aiohttp
```

## Configuration
Edit the configuration constants at the top of `main.py` before running the bot:

| Setting | Description |
| --- | --- |
| `TOKEN` | Discord bot token. Required for the bot to start. |
| `ROBLOX_COOKIE` | `.ROBLOSECURITY` cookie used for Roblox API requests. Required for developer presence polling and badge checks. |
| `GUILD_IDS` | Discord guild IDs where slash commands should be registered. |
| `CHANNEL_*` | Channel IDs for monitoring biome finds, announcing sightings, and posting status updates. |
| `ROLE_*` | Role IDs used in developer announcement pings. |
| `DEV_IDS`, `OWNER_IDS` | Roblox user IDs for developers and owners to watch. |
| `SOLS_RNG_GAME_ID` | Roblox universe ID for Sol's RNG, used to filter presence responses. |

Keep your Discord token and Roblox cookie private—never commit them to version control or share them publicly.

## Running the Bot
1. Configure the constants listed above.
2. Export the `TOKEN` and `ROBLOX_COOKIE` values as environment variables or set them directly in `main.py`.
3. Start the bot:

```bash
python main.py
```

The bot will log in, sync slash commands (globally and per guild), and begin polling Roblox every 1.3 minutes. Status updates are posted to the configured channel, and developer sightings trigger role-tagged embeds in the findings channel. 【main.py†L214-L330】

Press `Ctrl+C` to stop the bot gracefully. Background tasks are canceled, the Discord connection is closed cleanly, and shutdown is logged. 【main.py†L366-L390】

## Releases
Packaged builds of `main.py` are stored in the [`releases/`](releases) directory. Each file is a direct snapshot of the bot for distribution (for example, `main_v1.0.0.py`).

To cut a new release, copy the root `main.py` into the `releases/` directory with an appropriate semantic version suffix.

## Logging
Logs are written both to stdout and to `bot.log`. Adjust log levels by editing the `logging.basicConfig` call near the top of the file. 【main.py†L5-L44】

## Contributing
Pull requests and issues are welcome. When contributing:
- Run `python main.py` locally to ensure the bot starts without errors.
- Keep sensitive tokens out of commits.
- Update the `releases/` directory if your changes warrant a new versioned build.
