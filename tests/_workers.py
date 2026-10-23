"""Spawn-start worker functions (importable top-level, stdlib only)."""
from pathlib import Path

from lookup.store import open_store, upsert_word


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
