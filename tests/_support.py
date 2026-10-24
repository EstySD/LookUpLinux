"""Shared test helpers (stdlib only)."""
import os
import tempfile
from pathlib import Path
from unittest import mock

from lookup.store import MIGRATIONS

# The Phase 1 schema (user_version 1). Tests that mean "a version-1 database"
# open with migrations=V1, so they keep their meaning when later versions are added (D-35).
V1 = MIGRATIONS[:1]


def make_tempdir(testcase) -> Path:
    """Create a temp dir and point LOOKUP_DB, LOOKUP_DICTS, LOOKUP_CONFIG and
    LOOKUP_CACHE at not-yet-existing paths inside it (none is created here).

    Call it BEFORE opening any connection and register `conn.close` afterwards
    with `addCleanup`: cleanups run LIFO, so every connection is closed before
    Windows deletes the temp dir (RESEARCH Pitfall 6). The suite therefore never
    touches the real ~/.local/share/lookup/.
    """
    tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    testcase.addCleanup(tmp.cleanup)
    root = Path(tmp.name)
    patcher = mock.patch.dict(
        os.environ,
        {
            "LOOKUP_DB": str(root / "data" / "lookup" / "lookup.db"),
            "LOOKUP_DICTS": str(root / "dicts"),
            "LOOKUP_CONFIG": str(root / "config" / "config.json"),
            "LOOKUP_CACHE": str(root / "cache"),
        },
    )
    patcher.start()
    testcase.addCleanup(patcher.stop)
    return root


def forbid_network(testcase):
    """Make any urllib.request.urlopen call fail the test; return the mock.

    Tests assert `call_count == 0` on the result to prove a cache hit (D-20).
    """
    patcher = mock.patch(
        "urllib.request.urlopen", side_effect=AssertionError("network call attempted")
    )
    started = patcher.start()
    testcase.addCleanup(patcher.stop)
    return started
