"""Shared test helpers (stdlib only)."""
import os
import tempfile
from pathlib import Path
from unittest import mock


def make_tempdir(testcase) -> Path:
    """Create a temp dir and point LOOKUP_DB at a not-yet-existing file inside it.

    Call it BEFORE opening any connection and register `conn.close` afterwards
    with `addCleanup`: cleanups run LIFO, so every connection is closed before
    Windows deletes the temp dir (RESEARCH Pitfall 6). The suite therefore never
    touches the real ~/.local/share/lookup/.
    """
    tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    testcase.addCleanup(tmp.cleanup)
    root = Path(tmp.name)
    patcher = mock.patch.dict(
        os.environ, {"LOOKUP_DB": str(root / "data" / "lookup" / "lookup.db")}
    )
    patcher.start()
    testcase.addCleanup(patcher.stop)
    return root
