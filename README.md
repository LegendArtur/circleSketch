# CircleSketch

CircleSketch is a robust, production-ready Discord bot for running daily asynchronous art games. Players join a persistent circle, receive drawing prompts, submit their artwork via DM, and enjoy a polished gallery reveal. The bot supports scheduled, manual, and developer game modes, with reliable player management, persistent storage, and beautiful image generation for both prompts and galleries.

## Features
- Persistent player management with join/leave/list/reset commands
- Daily, manual, and developer game modes
- Scheduled games (via APScheduler)
- DM-based image submission and reminders
- Gallery and theme announcement image generation (Pillow)
- Robust, concurrent-safe storage (SQLite)
- Clear, colorized logging (colorama)
- Debug/test scripts for gallery output
- Full test suite with pytest

## Setup
1. **Clone the repository**
2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
3. **Configure environment variables**
   - Copy `.env.example` to `.env` and fill in your Discord bot token and channel ID.
   - Or set `DISCORD_TOKEN` and `GAME_CHANNEL_ID` as environment variables.
4. **Run the bot**
   - **Recommended:**
     ```sh
     python -m circle_sketch.main
     ```
   - **If your host does not support `-m` (e.g., some shared hosts):**
     ```sh
     python run_bot.py
     ```

## Production & Hosting
- The bot writes logs to both the console and a rotating file (`bot.log` by default).
- You can control the bot from the console with commands: `stop`, `status`, `help`.
- For 24/7 hosting, use a process manager (e.g., `screen`, `tmux`, or your host's panel).
- See `run_bot.py` for alternate launch instructions if needed.

## Configuration
- `circle_sketch/config.py`: Set up your Discord token, game channel, and other settings.
- `.env`: Store sensitive credentials (not committed to git).

## Commands
- `/join_circle` — Join the persistent player circle
- `/leave_circle` — Leave the circle
- `/list_circle` — List current circle members
- `/reset_circle` — [Admin] Reset the player circle
- `/start_scheduled_game` — Start daily scheduled games (5pm UTC)
- `/start_manual_game` — Start a manual game (ends manually)
- `/end_manual_game` — End a manual game
- `/dev_start_game` — [Dev] Start a single-user test game

## Game Flow
1. Players join the circle
2. At scheduled/manual/dev start, a theme is announced in the channel (with image)
3. Each player receives a DM prompt and submits their drawing as an image
4. Submissions are collected and announced in the channel
5. At the end, a gallery image is generated and posted

## Storage
- All persistent data (player circle, game state) is stored in `circle_sketch/storage.sqlite3` via `sqlite3`.
- No JSON files or in-memory state; safe for concurrent/multi-process use.

## Gallery Generation
- Uses Pillow to generate composite images for both theme announcements and gallery reveals.
- User avatars and drawing images are fetched and composed with dynamic sizing, colored borders, and bundled fonts for portability.

## Debugging
- `circle_sketch/debug_gallery.py` can be used to test gallery image output with local files.

## Testing
- Run all tests with:
  ```sh
  pytest
  ```
- Test output images are saved in `tests/output/` for manual inspection.

## Development
- Code is organized for clarity and maintainability.
- Logging is colorized for easy terminal reading.
- All major error sources are handled robustly.

## License
MIT License

---

*Built with ❤️ for asynchronous art games on Discord.*
