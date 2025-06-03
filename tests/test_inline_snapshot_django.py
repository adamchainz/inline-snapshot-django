from __future__ import annotations

from django.test import TestCase
from inline_snapshot import snapshot

from inline_snapshot_django import snapshot_queries
from tests.models import Character


class IndexTests(TestCase):
    databases = {"default", "other"}

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

    def test_other_database(self):
        with snapshot_queries(using="other") as snap:
            Character.objects.using("other").count()
        assert snap == snapshot(
            [
                "SELECT ... FROM tests_character",
            ]
        )

    def test_other_database_unused(self):
        with snapshot_queries(using="other") as snap:
            Character.objects.count()
        assert snap == snapshot([])

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
