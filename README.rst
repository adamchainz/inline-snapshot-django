======================
inline-snapshot-django
======================

.. image:: https://img.shields.io/github/actions/workflow/status/adamchainz/inline-snapshot-django/main.yml.svg?branch=main&style=for-the-badge
   :target: https://github.com/adamchainz/inline-snapshot-django/actions?workflow=CI

.. image:: https://img.shields.io/badge/Coverage-100%25-success?style=for-the-badge
   :target: https://github.com/adamchainz/inline-snapshot-django/actions?workflow=CI

.. image:: https://img.shields.io/pypi/v/inline-snapshot-django.svg?style=for-the-badge
   :target: https://pypi.org/project/inline-snapshot-django/

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
   :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=for-the-badge
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit

----

Extensions for using `inline-snapshot <https://github.com/15r10nk/inline-snapshot>`__ to test `Django <https://www.djangoproject.com/>`__ projects.

A quick example:

.. code-block:: python

    from django.test import TestCase
    from inline_snapshot import snapshot
    from inline_snapshot_django import snapshot_queries

    class IndexTests(TestCase):
        def test_success(self):
            with snapshot_queries() as snap:
                response = self.client.get("/")
            assert snap == snapshot(
                [
                    "SELECT ... FROM auth_user WHERE ...",
                    "SELECT ... FROM example_character WHERE ...",
                ]
            )

inline-snapshot will automatically capture and update the contents of ``snapshot()``, allowing you to quickly write and maintain tests that demonstrate the structure of your queries.
