from __future__ import annotations

import logging
from collections import defaultdict, deque
from collections.abc import Generator, Iterable
from contextlib import contextmanager

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
    log_filter = CaptureLogFilter(queries)
    sql_logger.addFilter(log_filter)
    sql_logger_level = sql_logger.level
    sql_logger.setLevel(logging.DEBUG)

    record: list[str | tuple[str, str]] = []
    try:
        yield record
    finally:
        sql_logger.removeFilter(log_filter)
        sql_logger.setLevel(sql_logger_level)

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


class CaptureLogFilter(logging.Filter):
    def __init__(self, queries: list[tuple[str, str]]) -> None:
        super().__init__()
        self.queries = queries

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            # Attributes added via extra by Django’s CursorDebugWrapper:
            # https://github.com/django/django/blob/b0c7d945ceae26590298b673033381cbe05ee475/django/db/backends/utils.py#L157-L162
            alias = record.alias  # type: ignore[attr-defined]
            sql = record.sql  # type: ignore[attr-defined]
        except AttributeError:  # pragma: no cover
            pass
        else:
            self.queries.append((alias, sql))
        return True
