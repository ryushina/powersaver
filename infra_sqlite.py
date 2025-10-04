# Minimal async-safe SQLite logger
import sqlite3, asyncio

class SQLiteLogRepo:
    def __init__(self, db_path: str = "tapo_log.db"):
        self.db_path = db_path
        self._init_once()

    def _init_once(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_time TEXT NOT NULL,
            current_count TEXT NOT NULL,
            is_tapo_on BOOLEAN NOT NULL
        )
        """)
        conn.commit()
        conn.close()

    async def log(self, date_time_iso: str, current_count: str, is_tapo_on: bool):
        def _insert():
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO logs (date_time, current_count, is_tapo_on)
            VALUES (?, ?, ?)
            """, (date_time_iso, current_count, 1 if is_tapo_on else 0))
            conn.commit()
            conn.close()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _insert)
