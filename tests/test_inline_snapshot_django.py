from django.test import TestCase
from inline_snapshot import snapshot
from inline_snapshot_django import snapshot_queries

from tests.models import Character


class IndexTests(TestCase):
    def test_single_query(self):
        with snapshot_queries() as snap:
            list(Character.objects.all())
        assert snap == snapshot(
            [
                "SELECT ... FROM tests_character",
            ]
        )

    def test_multiple_queries(self):
        with snapshot_queries() as snap:
            list(Character.objects.order_by("id"))
            list(Character.objects.order_by("-id"))
        assert snap == snapshot(
            [
                "SELECT ... FROM tests_character ORDER BY ... ASC",
                "SELECT ... FROM tests_character ORDER BY ... DESC",
            ]
        )
