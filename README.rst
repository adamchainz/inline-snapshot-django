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

            assert response.status_code == 200
            assert snap == snapshot(
                [
                    "SELECT ... FROM auth_user WHERE ...",
                    "SELECT ... FROM example_character WHERE ...",
                ]
            )

inline-snapshot will automatically capture and update the contents of ``snapshot()``, allowing you to quickly write and maintain tests that demonstrate the structure of your queries.

----

**Improve your Django and Git skills** with `my books <https://adamj.eu/books/>`__.

----

Requirements
============

Python 3.9 to 3.13 supported.

Django 4.2 to 5.2 supported.

Installation
============

With **pip**:

.. code-block:: sh

    python -m pip install inline-snapshot-django

There’s no need to add the package to your ``INSTALLED_APPS`` setting, as it does not act as a Django app.

Usage
=====

The primary interface is the ``snapshot_queries()`` context manager, which captures the SQL queries executed by Django, across all connections, and returns a list of their fingerprints.
This list can then be compared against a snapshot using |inline-snapshots snapshot() function|__, for example:

.. |inline-snapshots snapshot() function| replace:: inline-snapshot’s ``snapshot()`` function
__ https://15r10nk.github.io/inline-snapshot/latest/

.. code-block:: python

    from inline_snapshot import snapshot
    from inline_snapshot_django import snapshot_queries

    from example import Character


    class CharacterTests(TestCase):
        def test_all(self):
            with snapshot_queries() as snap:
                list(Character.objects.all())

            assert snap == snapshot()

When you first run such a test, it will fail and inline-snapshot will fill in the ``snapshot()`` call with the captured query list:

.. code-block:: console

    $ pytest
    ...
    tests/test_example.py .E...                                     [100%]

    ═══════════════════════════ inline-snapshot ═══════════════════════════
    ────────────────────────── Create snapshots ───────────────────────────
    ╭─────────────────────── tests/test_example.py ───────────────────────╮
    │ @@ -15,4 +15,4 @@                                                   │
    │                                                                     │
    │          with snapshot_queries() as snap:                           │
    │              list(Character.objects.all())                          │
    │                                                                     │
    │ -        assert snap == snapshot()                                  │
    │ +        assert snap == snapshot(["SELECT ... FROM tests_character" │
    ╰─────────────────────────────────────────────────────────────────────╯
    These changes will be applied, because you used create

inline-snapshot directly modifies the test file to replace the ``snapshot()`` call with the captured list.
You can then run the test again, and it will pass.

The system may later change its queries, for example to add or remove them, or to change their fingerprinted structure.
In that case, inline-snapshot will again fail the test, but offer to fix the snapshot with the new captured value:

.. code-block:: console

    $ pytest
    ...
    tests/test_example.py .E...                                     [100%]

    ═══════════════════════════ inline-snapshot ═══════════════════════════
    ──────────────────────────── Fix snapshots ────────────────────────────
    ╭─────────────────────── tests/test_example.py ───────────────────────╮
    │ @@ -16,4 +16,6 @@                                                   │
    │                                                                     │
    │              list(Character.objects.all())                          │
    │              list(Character.objects.all())                          │
    │                                                                     │
    │ -        assert snap == snapshot(["SELECT ... FROM tests_character" │
    │ +        assert snap == snapshot(                                   │
    │ +            ["SELECT ... FROM tests_character", "SELECT ... FROM t │
    │ +        )                                                          │
    ╰─────────────────────────────────────────────────────────────────────╯
    Do you want to fix these snapshots? [y/n] (n):

Follow the prompt to apply such changes.
This interactive prompt is only shown on interactive terminals with Python 3.11+.

inline-snapshot adds the ``--inline-snapshot`` option to pytest which controls the snapshot mode.
Use ``--inline-snapshot=update`` to automatically update snapshots without prompting.
See `the documentation <https://15r10nk.github.io/inline-snapshot/latest/pytest/>`__ for more details.

SQL fingerprints
----------------

SQL fingerprints are generated by `sql-impressao <https://pypi.org/project/sql-impressao/>`__, a wrapper around the `sql-fingerprint Rust crate <https://github.com/adamchainz/sql-fingerprint>`__.
It applies changes intended to make fingerprints stable even when you make small changes to your queries or database schema.
Some changes it makes:

* Identifier and value lists are reduced to '...'.
* Identifiers consisting of letters, numbers, and underscores have any quoting removed.
* Savepoint IDs are replaced with 's1', 's2', etc.

For a full list of the changes it makes, or to report fingerprinting issues, head to `the sql-fingerprint repository <https://github.com/adamchainz/sql-fingerprint>`__.

API
===

``snapshot_queries(*, using="__all__")``
----------------------------------------

Parameters:

* ``using: str | Iterable[str] = "__all__"``

  The database alias or aliases to capture queries for.
  The default is a special value, ``"__all__"``, which captures queries from all databases configured in Django's settings.

  Provide a single name to capture queries only from that database:

  .. code-block:: python

    with snapshot_queries(using="default") as snap:
        ...

  Provide an iterable of names to capture queries for only those databases:

  .. code-block:: python

    with snapshot_queries(using={"default", "other"}) as snap:
        ...

Returns:

* ``AbstractContextManager[list[str| tuple[str, str]]]``

  A context manager that returns a list.
  When the context exits, this list is populated with the fingerprints of the SQL queries executed within the context.

  For a query that ran on the default database, the entry will be just the fingerprint string:

  .. code-block:: python

    "SELECT ... FROM example_character WHERE ..."

  For queries that ran on a non-default database, the entry will be a tuple of the database alias and the fingerprint string:

  .. code-block:: python

    ("other", "SELECT ... FROM example_character WHERE ...")
