from __future__ import annotations

import contextvars
import re
from collections import defaultdict, deque
from collections.abc import Callable, Collection, Generator, Iterable
from contextlib import contextmanager
from functools import wraps
from types import MethodType
from typing import Any, Final, TypeVar, cast

import sql_impressao
from django.core.cache import caches
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


_CacheFunc = TypeVar("_CacheFunc", bound=Callable[..., Any])
_CACHE_METHODS: Final[tuple[str, ...]] = (
    "add",
    "decr",
    "delete",
    "delete_many",
    "get",
    "get_many",
    "get_or_set",
    "incr",
    "set",
    "set_many",
)
_CACHE_KEY_RE = re.compile(
    # Django session keys for 'cache' backend
    r"(?<=django\.contrib\.sessions\.cache)[0-9a-z]{32}\b"
    # Django session keys for 'cached_db' backend
    r"|(?<=django\.contrib\.sessions\.cached_db)[0-9a-z]{32}\b"
    # Long random hashes
    r"|\b[0-9a-f]{32}\b"
    # UUIDs
    r"|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    # Integers
    r"|\d+"
)
_is_internal_cache_call = contextvars.ContextVar(
    "is_internal_cache_call", default=False
)


@contextmanager
def snapshot_cache_ops(
    *,
    using: str | Iterable[str] = "__all__",
) -> Generator[list[tuple[str, str, str | list[str]]]]:
    if isinstance(using, str):
        if using == "__all__":
            aliases = list(caches)
        else:
            aliases = [using]
    else:
        aliases = list(using)

    record: list[tuple[str, str, str | list[str]]] = []

    def clean_key(key: str) -> str:
        return _CACHE_KEY_RE.sub("#", key)

    def call_callback(alias: str, func: _CacheFunc) -> _CacheFunc:
        @wraps(func)
        def inner(self: Any, *args: Any, **kwargs: Any) -> Any:
            if _is_internal_cache_call.get():
                return func(*args, **kwargs)

            if args:
                key_or_keys = args[0]
            elif "key" in kwargs:
                key_or_keys = kwargs["key"]
            else:
                key_or_keys = kwargs["keys"]

            cleaned_key_or_keys: str | list[str]
            if isinstance(key_or_keys, str):
                cleaned_key_or_keys = clean_key(key_or_keys)
            elif isinstance(key_or_keys, Collection):
                cleaned_key_or_keys = sorted(clean_key(k) for k in key_or_keys)
            else:
                raise ValueError("key_or_keys must be a string or collection")

            record.append((alias, str(func.__name__), cleaned_key_or_keys))

            token = _is_internal_cache_call.set(True)
            try:
                return func(*args, **kwargs)
            finally:
                _is_internal_cache_call.reset(token)

        return cast("_CacheFunc", inner)

    orig_methods = {}
    for alias in aliases:
        cache = caches[alias]
        orig_methods[alias] = {name: getattr(cache, name) for name in _CACHE_METHODS}
        for name in _CACHE_METHODS:
            orig_method = orig_methods[alias][name]
            setattr(cache, name, MethodType(call_callback(alias, orig_method), cache))

    yield record

    for alias in aliases:
        cache = caches[alias]
        for name in _CACHE_METHODS:
            setattr(cache, name, orig_methods[alias][name])
