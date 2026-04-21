import atexit
import sqlite3
import time
from collections import deque
from pathlib import Path

from .logger import logger


db_path = Path(__file__).parent.parent / "data" / "processed-listings.db"
db_path.parent.mkdir(parents=True, exist_ok=True)

# large in-mem cache
TEMP_SEEN_MAX_ITEMS = 250_000
TEMP_SEEN_TRIM_TO_ITEMS = 200_000

# batch size
SEEN_DB_COMMIT_BATCH_SIZE = 8

SEEN_DB_FORCE_COMMIT_INTERVAL_SECONDS = 20


class SeenItemsDB:
    def __init__(self, db_path: Path = db_path) -> None:
        self.db_path = db_path
        self.item_queue: list[tuple[str, int, str]] = []
        self.temp_seen: set[str] = set()
        self.temp_seen_order: deque[str] = deque()
        self.last_commit_time = time.time()
        self.init_db()
        atexit.register(self.commit_seen_items, True)

    def _add_temp_seen(self, item_id: str) -> None:
        if item_id in self.temp_seen:
            return

        self.temp_seen.add(item_id)
        self.temp_seen_order.append(item_id)
        self._trim_temp_seen_if_needed()

    def _trim_temp_seen_if_needed(self) -> None:
        if len(self.temp_seen) <= TEMP_SEEN_MAX_ITEMS:
            return

        removed_count = 0

        while len(self.temp_seen) > TEMP_SEEN_TRIM_TO_ITEMS and self.temp_seen_order:
            oldest_item_id = self.temp_seen_order.popleft()
            if oldest_item_id in self.temp_seen:
                self.temp_seen.remove(oldest_item_id)
                removed_count += 1

        if removed_count > 0:
            logger.debug(
                "Trimmed in-memory seen cache by %s entries (current size: %s)",
                removed_count,
                len(self.temp_seen),
            )

    def init_db(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS seen_items (
                        item_id        TEXT     PRIMARY KEY,
                        timestamp      INTEGER  NOT NULL,
                        title          TEXT
                    )
                    """
                )
                conn.commit()
            logger.debug(f"Seen-items database initialized at {self.db_path}")
        except Exception:
            logger.exception("Failed to initialize seen-items database:")
            raise

    def is_seen(self, item_id: str) -> bool:
        if item_id in self.temp_seen:
            return True

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM seen_items WHERE item_id = ?",
                    (item_id,),
                )
                is_in_db = cursor.fetchone() is not None

            if is_in_db:
                self._add_temp_seen(item_id)

            return is_in_db
        except Exception:
            logger.exception(f"Error checking if item {item_id} is seen:")
            return False

    def mark_seen(
        self,
        item_id: str,
        title: str = "",
    ) -> None:
        current_time = int(time.time())
        self.item_queue.append((item_id, current_time, title))
        self._add_temp_seen(item_id)
        logger.debug(f"Queued item {item_id} to be marked as seen")

    def commit_seen_items(self, force: bool = False) -> None:
        if not self.item_queue:
            return

        now = time.time()
        should_commit_for_size = len(self.item_queue) >= SEEN_DB_COMMIT_BATCH_SIZE
        should_commit_for_time = (now - self.last_commit_time) >= SEEN_DB_FORCE_COMMIT_INTERVAL_SECONDS

        if not force and not should_commit_for_size and not should_commit_for_time:
            return

        try:
            commit_count = len(self.item_queue)

            with sqlite3.connect(self.db_path) as conn:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO seen_items
                    (item_id, timestamp, title)
                    VALUES (?, ?, ?)
                    """,
                    self.item_queue,
                )
                conn.commit()

            logger.info(f"Committed {commit_count} items to the seen-items database")
            self.item_queue.clear()
            self.last_commit_time = now
        except Exception:
            logger.exception("Error committing seen items to database:")

    def cleanup_old_items(self, days_old: int = 30) -> int:
        try:
            cutoff_time = int(time.time()) - (days_old * 24 * 60 * 60)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM seen_items WHERE timestamp < ?",
                    (cutoff_time,),
                )
                deleted_count = cursor.rowcount
                conn.commit()

            logger.info(f"Cleaned up {deleted_count} seen items older than {days_old} days")
            return deleted_count
        except Exception:
            logger.exception("Error cleaning up old items:")
            return 0


seen_db = SeenItemsDB()
