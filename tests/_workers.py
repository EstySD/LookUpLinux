"""Spawn-start worker functions (importable top-level, stdlib only)."""
from pathlib import Path

from lookup.store import open_store, upsert_word
from tests._support import V1


def add_probe(conn):
    """Synthetic v1 -> v2 step (D-19)."""
    conn.execute("ALTER TABLE words ADD COLUMN probe TEXT")


def child(path, barrier, queue, index):
    """Open the store and upsert the same word; report the count or the error.

    Never re-raises: the parent inspects the queue results.
    """
    try:
        barrier.wait(timeout=30)
        conn = open_store(Path(path))
        try:
            count = upsert_word(
                conn, "run", translation="бежать", context="context %d" % index
            )
        finally:
            conn.close()
        queue.put(("ok", count))
    except BaseException as exc:  # noqa: BLE001 - reported to the parent
        queue.put(("err", type(exc).__name__ + ": " + str(exc)))


def migrate_child(path, barrier, queue):
    """Open a v1 store with a synthetic v2 step on top of the Phase 1 schema; report
    the resulting user_version or the error."""
    try:
        barrier.wait(timeout=30)
        conn = open_store(Path(path), migrations=V1 + (add_probe,))
        try:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
        finally:
            conn.close()
        queue.put(("ok", version))
    except BaseException as exc:  # noqa: BLE001 - reported to the parent
        queue.put(("err", type(exc).__name__ + ": " + str(exc)))
