import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


class DedupStore:
    def __init__(self, db_path: str, max_age_hours: int = 168):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.max_age_hours = max_age_hours
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_configs (
                config_hash TEXT PRIMARY KEY,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                config_type TEXT,
                raw_preview TEXT
            )
        """)
        self.conn.commit()

    def is_seen(self, config_hash: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM seen_configs WHERE config_hash = ?",
            (config_hash,),
        )
        return cur.fetchone() is not None

    def mark_seen(self, config_hash: str, config_type: str, raw_preview: str):
        self.conn.execute(
            "INSERT OR IGNORE INTO seen_configs (config_hash, config_type, raw_preview) VALUES (?, ?, ?)",
            (config_hash, config_type, raw_preview[:200]),
        )
        self.conn.commit()

    def purge_old(self):
        cutoff = datetime.utcnow() - timedelta(hours=self.max_age_hours)
        self.conn.execute(
            "DELETE FROM seen_configs WHERE first_seen < ?",
            (cutoff.isoformat(),),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
