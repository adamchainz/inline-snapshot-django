from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

import sql_impressao
from django.db import DEFAULT_DB_ALIAS, connections
from django.test.utils import CaptureQueriesContext


@contextmanager
def snapshot_queries(using: str = DEFAULT_DB_ALIAS) -> Generator[list[str]]:
    """
    Usage:
        with snapshot_queries() as queries:
            # code that runs queries
            ...
        assert queries == snapshot()
    """
    queries: list[str] = []
    with CaptureQueriesContext(connections[using]) as capture:
        yield queries

    queries[:] = sql_impressao.fingerprint_many(
        [q["sql"] for q in capture.captured_queries]
    )
