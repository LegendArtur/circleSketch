# SQLite storage logic

import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'storage.sqlite3')

class Storage:
    @staticmethod
    def _get_conn():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def init():
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS player_circle (
            user_id INTEGER PRIMARY KEY
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
        # Ensure group_streak row exists
        c.execute('INSERT OR IGNORE INTO group_streak (id, streak) VALUES (1, 0)')
        conn.commit()
        conn.close()

    @staticmethod
    def get_player_circle():
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('SELECT user_id FROM player_circle')
        result = [row['user_id'] for row in c.fetchall()]
        conn.close()
        return result

    @staticmethod
    def set_player_circle(circle):
        conn = Storage._get_conn()
        c = conn.cursor()
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
            return json.loads(row['state'])
        return None

    @staticmethod
    def set_game_state(state):
        conn = Storage._get_conn()
        c = conn.cursor()
        c.execute('DELETE FROM game_state')
        if state is not None:
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

Storage.init()
