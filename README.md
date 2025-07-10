# CircleSketch Discord Bot

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![discord.py](https://img.shields.io/badge/discord.py-2.3.2-7289DA.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

<p align="center">
  A collaborative daily drawing game for Discord.
</p>

**CircleSketch** is a robust Discord bot that hosts a daily drawing game. Players join a persistent circle to receive daily prompts, submit their art directly to the bot, and see a gallery of everyone's work at the end of the day. The bot is designed for 24/7 hosting, featuring streak tracking, admin controls, and a clean, modular codebase.

**Works out of the box with SQLite for local/dev use, or with MySQL for production/hosted deployments.**

-----

## Table of Contents

- [Features](#features)
- [Setup and Installation](#setup-and-installation)
- [Bot Commands](#bot-commands)
- [Customization](#customization)
- [Database Backend Selection](#database-backend-selection)
- [Contributing](#contributing)
- [License](#license)

-----

## Features

- 🎨 **Daily Drawing Game:** Automatically posts new prompts and reveals galleries at a configurable time.
- 🕹️ **Manual Game Mode:** Admins can start and end games on-demand with simple slash commands.
- 🔄 **Persistent Player Circle:** Users can easily join or leave the game circle at any time.
- 🖼️ **Dynamic Gallery Generation:** The bot collects submissions and generates themed gallery images for each player's art.
- 📈 **Streak Tracking:** Motivates players by tracking both group participation streaks and individual user stats.
- 🛡️ **Admin Controls:** Provides necessary tools for moderation, including resetting the player circle and checking game status.
- ⚙️ **Production Ready:** Includes robust logging, graceful shutdown handling, and a modular, extensible codebase built with `discord.py` cogs.

-----

## Setup and Installation

### Prerequisites

  * Python 3.10+
  * Git

### 1\. Clone the Repository

```bash
git clone https://github.com/your-username/CircleSketch.git
cd CircleSketch
```

### 2\. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3\. Create Your Prompt List

The bot uses a simple Python list for its drawing prompts. To keep your list private, it is not tracked by Git.

1.  **Copy the example file:**

    ```bash
    cp circle_sketch/prompts.example.py circle_sketch/prompts.py
    ```

2.  **Edit `circle_sketch/prompts.py`** and add your own list of prompts.

    *Example `prompts.py`*:

    ```python
    # This list contains the drawing prompts for the bot.
    PROMPT_LIST = [
        "A happy cat wearing a top hat",
        "A robot chef making pancakes",
        "A majestic dragon flying over a futuristic city",
    ]
    ```

### 4\. Configure Environment Variables

Create a `.env` file in the root directory of the project to store your bot's credentials and configuration.

```env
# .env
DISCORD_TOKEN=your-super-secret-bot-token
GAME_CHANNEL_ID=your-game-channel-id

# Optional: Override default settings
# LOG_FILE=logs/bot.log
# SCHEDULED_GAME_TIME=17:00
```

### 5\. Run the Bot

```bash
python run_bot.py
```

-----

## Bot Commands

| Command                 | Description                                                  | Permissions |
| ----------------------- | ------------------------------------------------------------ | ----------- |
| `/join_circle`          | Join the player circle to participate in games.              | All Users   |
| `/leave_circle`         | Leave the player circle.                                     | All Users   |
| `/list_circle`          | Lists all current members of the player circle.              | All Users   |
| `/show_streaks`         | Displays the current group streak and individual stats.      | All Users   |
| `/game_status`          | Shows the status of the current game, including the theme.   | All Users   |
| `/start_manual_game`    | Manually starts a new game that runs until ended.            | All Users   |
| `/end_manual_game`      | Ends the current manual game and posts the gallery.          | Game Starter or Admin |
| `/reset_circle`         | **[Admin]** Resets the player circle, removing all members.  | Admin Only  |

-----

## Customization

  * **Prompts:** Keep your prompt list unique and private by editing only your local `prompts.py`.
  * **Assets:** Place custom fonts in `assets/fonts/` to change the look of the generated gallery images.
  * **Configuration:** Most core settings (like game time) can be adjusted in your `.env` file or directly in `circle_sketch/config.py`.

-----

## Database Backend Selection

CircleSketch supports both SQLite (default, for local/dev use) and MySQL (for production, e.g., PebbleHost) as storage backends. The backend is selected at runtime using an environment variable.

### Quick Start (SQLite, recommended for forks and local dev)
No setup required. SQLite is used by default. Just run:

```
python run_bot.py
```

### Production/Host Setup (MySQL)
1. Install MySQL and create a database/user, or use your host's MySQL credentials.
2. Install the required Python package:
   ```
   pip install mysql-connector-python
   ```
3. Set the following environment variables:
   - `CIRCLE_SKETCH_DB_BACKEND=mysql`
   - `CIRCLE_SKETCH_MYSQL_URL=mysql://user:pass@host/db`
4. Run the bot as usual:
   ```
   python run_bot.py
   ```

### How it works
- The bot will automatically use SQLite unless you set `CIRCLE_SKETCH_DB_BACKEND` to `mysql`.
- All code uses the same `Storage` interface, so you do not need to change any code to switch backends.
- This makes it easy for open source contributors to run the bot locally, and for production users to use a robust, scalable database.

### Adding More Backends
You can add more backends (e.g., PostgreSQL) by implementing the same storage API and updating `storage/storage.py`.

---

**Tip:** If you want to force SQLite for demo/testing, set:
```
CIRCLE_SKETCH_DB_BACKEND=sqlite python run_bot.py
```

**For more details, see the `storage/` directory and code comments.**

-----

## Contributing

Contributions are welcome\! Please feel free to fork the repository, create a new branch, and submit a pull request. When contributing, please do not commit your personal `prompts.py` file.

-----

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/LegendArtur/circleSketch/blob/main/LICENSE) file for details.