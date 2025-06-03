from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

import sql_impressao
from django.core.signals import request_started
from django.db import DEFAULT_DB_ALIAS, connections, reset_queries
from django.db.backends.utils import logger as sql_logger


@contextmanager
def snapshot_queries(using: str = DEFAULT_DB_ALIAS) -> Generator[list[str]]:
    """
    Usage:
        with snapshot_queries() as queries:
            # code that runs queries
            ...
        assert queries == snapshot()
    """

    # State management copied from Django’s CaptureQueriesContext
    connection = connections[using]
    force_debug_cursor = connection.force_debug_cursor
    connection.force_debug_cursor = True
    connection.ensure_connection()
    reset_queries_disconnected = request_started.disconnect(reset_queries)

    queries: list[str] = []
    log_filter = CaptureLogFilter(queries)
    sql_logger.addFilter(log_filter)
    sql_logger_level = sql_logger.level
    sql_logger.setLevel(logging.DEBUG)

    record: list[str] = []
    try:
        yield record
    finally:
        sql_logger.removeFilter(log_filter)
        sql_logger.setLevel(sql_logger_level)
        if reset_queries_disconnected:
            request_started.connect(reset_queries)
        connection.force_debug_cursor = force_debug_cursor

    record[:] = sql_impressao.fingerprint_many(queries)


class CaptureLogFilter(logging.Filter):
    def __init__(self, queries: list[str]) -> None:
        super().__init__()
        self.queries = queries

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            sql = record.sql  # type: ignore[attr-defined]
        except AttributeError:  # pragma: no cover
            pass
        else:
            self.queries.append(sql)
        return True
