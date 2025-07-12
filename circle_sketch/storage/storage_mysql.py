# MySQL storage logic for CircleSketch
# Requires: pip install mysql-connector-python
import mysql.connector
import json
import os
import sys

MYSQL_URL = os.environ.get("CIRCLE_SKETCH_MYSQL_URL")
if not MYSQL_URL:
    raise RuntimeError("CIRCLE_SKETCH_MYSQL_URL must be set for MySQL backend.")

# Parse URL: mysql://user:pass@host/db
import re
m = re.match(r"mysql://([^:]+):([^@]+)@([^/]+)/(.+)", MYSQL_URL)
if not m:
    raise RuntimeError("CIRCLE_SKETCH_MYSQL_URL must be in format mysql://user:pass@host/db")
MYSQL_USER, MYSQL_PASS, MYSQL_HOST, MYSQL_DB = m.groups()

class MySQLStorage:
    @staticmethod
    def _get_conn():
        try:
            return mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASS,
                database=MYSQL_DB,
                autocommit=True
            )
        except Exception as e:
            print(f"[FATAL] Could not connect to MySQL: {e}", file=sys.stderr)
            sys.exit(1)

    @staticmethod
    def init():
        try:
            conn = MySQLStorage._get_conn()
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS player_circle (
                user_id BIGINT,
                guild_id BIGINT,
                PRIMARY KEY (user_id, guild_id)
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS game_state (
                id INT PRIMARY KEY,
                state TEXT
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS user_stats (
                user_id BIGINT PRIMARY KEY,
                submissions INT DEFAULT 0
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS group_streak (
                id INT PRIMARY KEY,
                streak INT DEFAULT 0
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS bot_flags (
                `key` VARCHAR(64) PRIMARY KEY,
                value VARCHAR(64)
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS user_streaks (
                user_id BIGINT PRIMARY KEY,
                streak INT DEFAULT 0
            )''')
            c.execute('INSERT IGNORE INTO group_streak (id, streak) VALUES (1, 0)')
            c.execute('INSERT IGNORE INTO bot_flags (`key`, value) VALUES ("first_game_started", "0")')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[FATAL] MySQL init failed: {e}", file=sys.stderr)
            sys.exit(1)

    @staticmethod
    def get_player_circle(guild_id=None):
        conn = MySQLStorage._get_conn()
        c = conn.cursor(dictionary=True)
        if guild_id is not None:
            c.execute('SELECT user_id FROM player_circle WHERE guild_id=%s', (guild_id,))
        else:
            c.execute('SELECT user_id FROM player_circle')
        result = [row['user_id'] for row in c.fetchall()]
        conn.close()
        return result

    @staticmethod
    def set_player_circle(guild_id, circle):
        conn = MySQLStorage._get_conn()
        c = conn.cursor()
        c.execute('DELETE FROM player_circle WHERE guild_id=%s', (guild_id,))
        if circle:
            c.executemany('INSERT INTO player_circle (user_id, guild_id) VALUES (%s, %s)', [(uid, guild_id) for uid in circle])
        conn.commit()
        conn.close()

    @staticmethod
    def get_game_state():
        conn = MySQLStorage._get_conn()
        c = conn.cursor(dictionary=True)
        c.execute('SELECT state FROM game_state WHERE id=1')
        row = c.fetchone()
        conn.close()
        if row and row['state']:
            state = json.loads(row['state'])
            if 'manual_game_starter_id' not in state:
                state['manual_game_starter_id'] = None
            return state
        return None

    @staticmethod
    def set_game_state(state):
        conn = MySQLStorage._get_conn()
        c = conn.cursor()
        c.execute('DELETE FROM game_state WHERE id=1')
        if state is not None:
            if 'manual_game_starter_id' not in state:
                state['manual_game_starter_id'] = None
            c.execute('INSERT INTO game_state (id, state) VALUES (1, %s)', (json.dumps(state),))
        conn.commit()
        conn.close()

    @staticmethod
    def reset():
        # This will need a guild_id if you want to reset per-guild
        MySQLStorage.set_player_circle(None, [])
        MySQLStorage.set_game_state(None)

    @staticmethod
    def clear_all():
        conn = MySQLStorage._get_conn()
        c = conn.cursor()
        c.execute('DELETE FROM player_circle')
        c.execute('DELETE FROM game_state')
        conn.commit()
        conn.close()

    @staticmethod
    def get_user_stats():
        conn = MySQLStorage._get_conn()
        c = conn.cursor(dictionary=True)
        c.execute('SELECT user_id, submissions FROM user_stats')
        stats = {row['user_id']: row['submissions'] for row in c.fetchall()}
        conn.close()
        return stats

    @staticmethod
    def increment_user_submission(user_id):
        conn = MySQLStorage._get_conn()
        c = conn.cursor()
        c.execute('INSERT INTO user_stats (user_id, submissions) VALUES (%s, 1) ON DUPLICATE KEY UPDATE submissions = submissions + 1', (user_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_group_streak():
        conn = MySQLStorage._get_conn()
        c = conn.cursor(dictionary=True)
        c.execute('SELECT streak FROM group_streak WHERE id=1')
        row = c.fetchone()
        conn.close()
        return row['streak'] if row else 0

    @staticmethod
    def set_group_streak(streak):
        conn = MySQLStorage._get_conn()
        c = conn.cursor()
        c.execute('UPDATE group_streak SET streak=%s WHERE id=1', (streak,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_first_game_started():
        conn = MySQLStorage._get_conn()
        c = conn.cursor(dictionary=True)
        c.execute('SELECT value FROM bot_flags WHERE `key`="first_game_started"')
        row = c.fetchone()
        conn.close()
        return row['value'] == '1' if row else False

    @staticmethod
    def set_first_game_started(val: bool):
        conn = MySQLStorage._get_conn()
        c = conn.cursor()
        c.execute('UPDATE bot_flags SET value=%s WHERE `key`="first_game_started"', ("1" if val else "0",))
        conn.commit()
        conn.close()

    @staticmethod
    def get_user_streak(user_id):
        conn = MySQLStorage._get_conn()
        c = conn.cursor(dictionary=True)
        c.execute('SELECT streak FROM user_streaks WHERE user_id=%s', (user_id,))
        row = c.fetchone()
        conn.close()
        return row['streak'] if row else 0

    @staticmethod
    def set_user_streak(user_id, streak):
        conn = MySQLStorage._get_conn()
        c = conn.cursor()
        c.execute('INSERT INTO user_streaks (user_id, streak) VALUES (%s, %s) ON DUPLICATE KEY UPDATE streak=%s', (user_id, streak, streak))
        conn.commit()
        conn.close()

    @staticmethod
    def reset_all_streaks():
        conn = MySQLStorage._get_conn()
        c = conn.cursor()
        c.execute('UPDATE group_streak SET streak=0 WHERE id=1')
        c.execute('UPDATE user_streaks SET streak=0')
        conn.commit()
        conn.close()

    @staticmethod
    async def download_image(url):
        """Download an image from a Discord URL to a temp file and return the file path."""
        import aiohttp, tempfile
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

MySQLStorage.init()
