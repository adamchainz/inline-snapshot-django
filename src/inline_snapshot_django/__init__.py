from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from typing import Any

import sql_impressao
from django.core.signals import request_started
from django.db import DEFAULT_DB_ALIAS, connections, reset_queries
from django.db.backends.utils import logger as sql_logger


@contextmanager
def snapshot_queries(
    *,
    using: str | Iterable[str] = "__all__",
) -> Generator[list[str | tuple[str, str]]]:
    if isinstance(using, str):
        if using == "__all__":
            aliases = list(connections)
        else:
            aliases = [using]
    else:
        aliases = list(using)

    # State management copied from Django’s CaptureQueriesContext
    force_debug_cursors = []
    for alias in aliases:
        connection = connections[alias]
        force_debug_cursors.append(connection.force_debug_cursor)
        connection.force_debug_cursor = True
        connection.ensure_connection()

    reset_queries_disconnected = request_started.disconnect(reset_queries)

    queries: list[tuple[str, str]] = []
    record: list[str | tuple[str, str]] = []
    try:
        with _capture_debug_logged_queries(aliases, queries):
            yield record
    finally:
        if reset_queries_disconnected:
            request_started.connect(reset_queries)

        for alias, force_debug_cursor in zip(aliases, force_debug_cursors):
            connection = connections[alias]
            connection.force_debug_cursor = force_debug_cursor

    queries_by_alias = defaultdict(list)
    for alias, sql in queries:
        queries_by_alias[alias].append(sql)
    formatted_queries_by_alias = {}
    for alias in aliases:
        if alias not in queries_by_alias:
            continue
        # Use sql_impressao to format the SQL queries
        formatted_queries_by_alias[alias] = deque(
            sql_impressao.fingerprint_many(queries_by_alias[alias])
        )

    for alias, _ in queries:
        entry = formatted_queries_by_alias[alias].popleft()
        if alias != DEFAULT_DB_ALIAS:
            entry = (alias, entry)
        record.append(entry)


@contextmanager
def _capture_debug_logged_queries(
    aliases: list[str], queries: list[tuple[str, str]]
) -> Generator[None]:
    """
    Wrap the debug() method of Django’s logger to intercept calls and capture
    the logged SQL queries.

    This is done instead of using a custom logging filter to avoid modifying
    the global logger configuration and to avoid adding logs to test output.
    """
    alias_set = set(aliases)
    original_debug = sql_logger.debug

    def debug_wrapper(*args: Any, extra: Any = None, **kwargs: Any) -> Any:
        if isinstance(extra, dict) and "alias" in extra and "sql" in extra:
            alias = extra["alias"]
            sql = extra["sql"]
            if alias in alias_set:
                queries.append((alias, sql))
        return original_debug(*args, extra=extra, **kwargs)

    sql_logger.debug = debug_wrapper  # type: ignore[method-assign]

    try:
        yield
    finally:
        sql_logger.debug = original_debug  # type: ignore[method-assign]
