from __future__ import annotations

import inspect
import threading
from textwrap import dedent
from unittest import expectedFailure

import django
import pytest
from django.db.backends.utils import logger as sql_logger
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from inline_snapshot import snapshot

from inline_snapshot_django import snapshot_queries
from tests.models import Character


class SnapshotQueriesTests(TestCase):
    databases = {"default", "other"}

    @pytest.mark.skipif(django.VERSION < (5, 2), reason="Django 5.2+")
    def test_capture_queries_context_source(self):
        """
        snapshot_queries() copied a lot of code from the upstream
        CaptureQueriesContext, so check for any upstream changes that may be
        worth copying over.
        """
        source = dedent(inspect.getsource(CaptureQueriesContext))
        expected = dedent(
            '''\
            class CaptureQueriesContext:
                """
                Context manager that captures queries executed by the specified connection.
                """

                def __init__(self, connection):
                    self.connection = connection

                def __iter__(self):
                    return iter(self.captured_queries)

                def __getitem__(self, index):
                    return self.captured_queries[index]

                def __len__(self):
                    return len(self.captured_queries)

                @property
                def captured_queries(self):
                    return self.connection.queries[self.initial_queries : self.final_queries]

                def __enter__(self):
                    self.force_debug_cursor = self.connection.force_debug_cursor
                    self.connection.force_debug_cursor = True
                    # Run any initialization queries if needed so that they won't be
                    # included as part of the count.
                    self.connection.ensure_connection()
                    self.initial_queries = len(self.connection.queries_log)
                    self.final_queries = None
                    request_started.disconnect(reset_queries)
                    return self

                def __exit__(self, exc_type, exc_value, traceback):
                    self.connection.force_debug_cursor = self.force_debug_cursor
                    request_started.connect(reset_queries)
                    if exc_type is not None:
                        return
                    self.final_queries = len(self.connection.queries_log)
            '''
        )
        assert source == expected

    def test_ignored_logging_messages(self):
        """
        Various unknown usage of the sql logger should result in any captured queries
        """
        with snapshot_queries() as snap:
            sql_logger.debug("what")
            sql_logger.debug("what", extra=12)  # type: ignore[arg-type]
            sql_logger.debug("what", extra={})
            sql_logger.debug("what", extra={"alias": "default"})
            sql_logger.debug("what", extra={"sql": "SELECT 1"})
            sql_logger.debug("what", extra={"alias": "unknown", "sql": "SELECT 1"})

        assert snap == snapshot([])

    def test_single_query(self):
        with snapshot_queries() as snap:
            Character.objects.count()
        assert snap == snapshot(
            [
                "SELECT ... FROM tests_character",
            ]
        )

    def test_multiple_queries(self):
        with snapshot_queries() as snap:
            Character.objects.count()
            Character.objects.count()
        assert snap == snapshot(
            [
                "SELECT ... FROM tests_character",
                "SELECT ... FROM tests_character",
            ]
        )

    def test_multiple_databases(self):
        with snapshot_queries() as snap:
            Character.objects.using("default").count()
            Character.objects.using("other").count()
            Character.objects.using("default").count()
            Character.objects.using("other").count()

        assert snap == snapshot(
            [
                "SELECT ... FROM tests_character",
                ("other", "SELECT ... FROM tests_character"),
                "SELECT ... FROM tests_character",
                ("other", "SELECT ... FROM tests_character"),
            ]
        )

    def test_using_default_database(self):
        with snapshot_queries(using="default") as snap:
            Character.objects.count()
            Character.objects.using("other").count()
        assert snap == snapshot(
            [
                "SELECT ... FROM tests_character",
            ]
        )

    def test_using_other_database(self):
        with snapshot_queries(using="other") as snap:
            Character.objects.using("other").count()
        assert snap == snapshot(
            [
                ("other", "SELECT ... FROM tests_character"),
            ]
        )

    def test_using_other_database_unused(self):
        with snapshot_queries(using="other") as snap:
            Character.objects.count()
        assert snap == snapshot([])

    def test_using_multiple_databases(self):
        with snapshot_queries(using={"default", "other"}) as snap:
            Character.objects.count()
            Character.objects.using("other").count()
        assert snap == snapshot(
            [
                "SELECT ... FROM tests_character",
                ("other", "SELECT ... FROM tests_character"),
            ]
        )

    def test_nested(self):
        with snapshot_queries() as snap:
            Character.objects.count()
            with snapshot_queries() as snap2:
                Character.objects.count()
        assert snap == snapshot(
            [
                "SELECT ... FROM tests_character",
                "SELECT ... FROM tests_character",
            ]
        )
        assert snap2 == snapshot(
            [
                "SELECT ... FROM tests_character",
            ]
        )

    @expectedFailure
    def test_threads(self):
        def thread_func():
            Character.objects.count()

        with snapshot_queries() as snap:
            thread = threading.Thread(target=thread_func)
            thread.start()
            thread.join()

        assert snap == [
            "SELECT ... FROM tests_character",
        ]
