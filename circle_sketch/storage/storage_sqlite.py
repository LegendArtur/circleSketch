# SQLite storage logic

import sqlite3
import json
import os
import sys
import tempfile
import aiohttp

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'storage.sqlite3')

class Storage:
    @staticmethod
    def _get_conn():
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"[FATAL] Could not connect to SQLite: {e}", file=sys.stderr)
            sys.exit(1)

    @staticmethod
    def init():
        try:
            conn = Storage._get_conn()
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS player_circle (
                user_id INTEGER PRIMARY KEY,
                guild_id INTEGER
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS game_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                state TEXT
            )''')
            # New: Table for per-user submission stats
            c.execute('''CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                submissions INTEGER DEFAULT 0
            )''')
            # New: Table for group streak
            c.execute('''CREATE TABLE IF NOT EXISTS group_streak (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                streak INTEGER DEFAULT 0
            )''')
            # New: Table for first_game_started flag
            c.execute('''CREATE TABLE IF NOT EXISTS bot_flags (
                key TEXT PRIMARY KEY,
                value TEXT
            )''')
            # New: Table for per-user streaks
            c.execute('''CREATE TABLE IF NOT EXISTS user_streaks (
                user_id INTEGER PRIMARY KEY,
                streak INTEGER DEFAULT 0
            )''')
            # Ensure group_streak row exists
            c.execute('INSERT OR IGNORE INTO group_streak (id, streak) VALUES (1, 0)')
            # Ensure first_game_started flag exists
            c.execute('INSERT OR IGNORE INTO bot_flags (key, value) VALUES ("first_game_started", "0")')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[FATAL] SQLite init failed: {e}", file=sys.stderr)
            sys.exit(1)

    @staticmethod
    def get_player_circle(guild_id=None):
        conn = Storage._get_conn()
        c = conn.cursor()
        if guild_id is not None:
            c.execute('SELECT user_id FROM player_circle WHERE guild_id=?', (guild_id,))
        else:
            c.execute('SELECT user_id FROM player_circle')
        result = [row['user_id'] for row in c.fetchall()]
        conn.close()
        return result

    @staticmethod
    def set_player_circle(guild_id, circle):
        conn = Storage._get_conn()
        c = conn.cursor()
        if guild_id is not None:
            c.execute('DELETE FROM player_circle WHERE guild_id=?', (guild_id,))
            c.executemany('INSERT INTO player_circle (user_id, guild_id) VALUES (?, ?)', [(uid, guild_id) for uid in circle])
        else:
            c.execute('DELETE FROM player_circle')
            c.executemany('INSERT INTO player_circle (user_id) VALUES (?)', [(uid,) for uid in circle])
        conn.commit()
        conn.close()

    @staticmethod
    def get_game_state():
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('SELECT state FROM game_state WHERE id=1')
        row = c.fetchone()
        conn.close()
        if row and row['state']:
            state = json.loads(row['state'])
            # Ensure manual_game_starter_id is present for compatibility
            if 'manual_game_starter_id' not in state:
                state['manual_game_starter_id'] = None
            return state
        return None

    @staticmethod
    def set_game_state(state):
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('DELETE FROM game_state')
        if state is not None:
            # Always include manual_game_starter_id for persistence
            if 'manual_game_starter_id' not in state:
                state['manual_game_starter_id'] = None
            c.execute('INSERT INTO game_state (id, state) VALUES (1, ?)', (json.dumps(state),))
        conn.commit()
        conn.close()

    @staticmethod
    def reset():
        Storage.set_player_circle([])
        Storage.set_game_state(None)

    @staticmethod
    def clear_all():
        """Completely clear all persistent game/player data but keep DB structure."""
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('DELETE FROM player_circle')
        c.execute('DELETE FROM game_state')
        conn.commit()
        conn.close()

    @staticmethod
    def get_user_stats():
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('SELECT user_id, submissions FROM user_stats')
        stats = {row['user_id']: row['submissions'] for row in c.fetchall()}
        conn.close()
        return stats

    @staticmethod
    def increment_user_submission(user_id):
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('INSERT INTO user_stats (user_id, submissions) VALUES (?, 1) ON CONFLICT(user_id) DO UPDATE SET submissions = submissions + 1', (user_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_group_streak():
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('SELECT streak FROM group_streak WHERE id=1')
        row = c.fetchone()
        conn.close()
        return row['streak'] if row else 0

    @staticmethod
    def set_group_streak(streak):
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('UPDATE group_streak SET streak=? WHERE id=1', (streak,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_first_game_started():
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('SELECT value FROM bot_flags WHERE key="first_game_started"')
        row = c.fetchone()
        conn.close()
        return row['value'] == '1' if row else False

    @staticmethod
    def set_first_game_started(val: bool):
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('UPDATE bot_flags SET value=? WHERE key="first_game_started"', ("1" if val else "0",))
        conn.commit()
        conn.close()

    @staticmethod
    def get_user_streak(user_id):
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('SELECT streak FROM user_streaks WHERE user_id=?', (user_id,))
        row = c.fetchone()
        conn.close()
        return row['streak'] if row else 0

    @staticmethod
    def set_user_streak(user_id, streak):
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('INSERT INTO user_streaks (user_id, streak) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET streak=?', (user_id, streak, streak))
        conn.commit()
        conn.close()

    @staticmethod
    def reset_all_streaks():
        """Reset both group and all user streaks to zero."""
        conn = Storage._get_conn()
        c = conn.cursor()
        # Reset group streak
        c.execute('UPDATE group_streak SET streak=0 WHERE id=1')
        # Reset all user streaks
        c.execute('UPDATE user_streaks SET streak=0')
        conn.commit()
        conn.close()

    @staticmethod
    async def download_image(url):
        """Download an image from a Discord URL to a temp file and return the file path."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise Exception(f"Failed to download image: {resp.status}")
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                        tmp.write(await resp.read())
                        return tmp.name
        except Exception as e:
            raise Exception(f"Error downloading image: {e}")

Storage.init()
