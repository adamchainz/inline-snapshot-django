Usage
=====

The primary interface of inline-snapshot is the :func:`.snapshot_queries` context manager, which captures SQL queries executed through Django and returns a list of their fingerprints.
This list can then be compared against a snapshot using |inline-snapshots snapshot() function|__.

.. |inline-snapshots snapshot() function| replace:: inline-snapshot’s ``snapshot()`` function
__ https://15r10nk.github.io/inline-snapshot/latest/

This page covers several ways to use ``snapshot_queries()``.

Add snapshots to a test
-----------------------

To add query snapshotting to a test, first:

1. Write your test in the usual way: call your system-under-test, such as a Django view or model method, and include any typical assertions.
2. Wrap the call to your system-under-test in a ``with`` block that uses the :func:`.snapshot_queries` context manager, assigning its return value to a variable, recommended name: ``snap``.
3. Add an assertion that compares that variable against inline-snapshot’s ``snapshot()`` function.
   This is best done after your other assertions, to ensure that the system-under-test behaves as expected before checking how it achieved that behaviour.

For example:

.. code-block:: python
   :emphasize-lines: 2,3,8,12

   from django.test import TestCase
   from inline_snapshot import snapshot
   from inline_snapshot_django import snapshot_queries


   class IndexTests(TestCase):
       def test_success(self):
           with snapshot_queries() as snap:
               response = self.client.get("/")

           assert response.status_code == 200
           assert snap == snapshot()


Then, run the test.
It will fail and inline-snapshot will fill in the ``snapshot()`` call with the captured fingerprints query list:

.. code-block:: text

    $ pytest
    ...
    example/tests.py .E                                             [100%]

    ═══════════════════════════ inline-snapshot ═══════════════════════════
    ────────────────────────── Create snapshots ───────────────────────────
    ╭───────────────────────── example/tests.py ──────────────────────────╮
    │ @@ -9,4 +9,9 @@                                                     │
    │                                                                     │
    │              response = self.client.get("/")                        │
    │                                                                     │
    │          assert response.status_code == 200                         │
    │ -        assert snap == snapshot()                                  │
    │ +        assert snap == snapshot(                                   │
    │ +            [                                                      │
    │ +                "SELECT ... FROM example_character",               │
    │ +                "SELECT ... FROM example_character LIMIT ...",     │
    │ +            ]                                                      │
    │ +        )                                                          │
    ╰─────────────────────────────────────────────────────────────────────╯
    These changes will be applied, because you used create
    ...
    ======================= short test summary info =======================
    ERROR example/tests.py::IndexTests::test_success - Failed: your snapshot is missing one value.
    ===================== 1 passed, 1 error in 0.09s ======================

The message “These changes will be applied, because you used create” indicates that inline-snapshot will fill in the empty ``snapshot()`` call with the captured query list.

inline-snapshot separates potential snapshot changes into different `categories <https://15r10nk.github.io/inline-snapshot/latest/categories/>`__.
When used in an interactive terminal, it defaults to applying **create** changes, where it fills in empty ``snapshot()`` calls with the captured values.

You’ll see that your test file has been modified to include the captured SQL query fingerprints in the ``snapshot()`` call:

.. code-block:: diff

             assert response.status_code == 200
    -        assert snap == snapshot()
    +        assert snap == snapshot(
    +            [
    +                "SELECT ... FROM example_character",
    +                "SELECT ... FROM example_character LIMIT ...",
    +            ]
    +        )

Run the test again and it will pass:

.. code-block:: text

    $ pytest
    ...
    tests/test_example.py .                                         [100%]

    1 passed in 0.01s

Now you’re free to commit this test.

Update tests interactively
--------------------------

Your system may later change its queries, for example to add or remove them, or to change their fingerprinted structures.
When such changes occur, your tests will fail until you update the snapshots to match the new queries.

In non-interactive terminals, such as in a Continuous Integration (CI) environment, inline-snapshot will default to using its **report** mode.
In this case, a mismatch between the captured queries and the snapshot will report the differences, but will not modify the test file, like:

.. code-block:: text

    $ pytest
    ...
    example/tests.py FE                                             [100%]

    ═══════════════════════════ inline-snapshot ═══════════════════════════
    ──────────────────────────── Fix snapshots ────────────────────────────
    ╭───────────────────────── example/tests.py ──────────────────────────╮
    │ @@ -12,6 +12,6 @@                                                   │
    │                                                                     │
    │          assert snap == snapshot(                                   │
    │              [                                                      │
    │                  "SELECT ... FROM example_character",               │
    │ -                "SELECT ... FROM example_character LIMIT ...",     │
    │ +                "SELECT ... FROM example_character LEFT OUTER JOIN │
    │              ]                                                      │
    │          )                                                          │
    ╰─────────────────────────────────────────────────────────────────────╯
    These changes are not applied.
    Use --inline-snapshot=fix to apply them, or use the interactive mode
    with --inline-snapshot=review
    ...
    ======================= short test summary info =======================
    FAILED example/tests.py::IndexTests::test_success - AssertionError: assert ['SELECT ... ..... LIMIT ...'] == ['SELECT ...
    ERROR example/tests.py::IndexTests::test_success - Failed: some snapshots in this test have incorrect values.
    ===================== 1 failed, 1 error in 0.08s ======================

In interactive terminals, like your local development environment, inline-snapshot will default to using its **review** mode (unless pytest-xdist is active, per `inline-snapshot’s limitations <https://15r10nk.github.io/inline-snapshot/latest/limitations/>`__).
Review mode will prompt you about any snapshot differences and offer to apply them interactively:

.. code-block:: text

    $ pytest
    ...
    example/tests.py .E                                             [100%]

    ═══════════════════════════ inline-snapshot ═══════════════════════════
    ──────────────────────────── Fix snapshots ────────────────────────────
    ╭───────────────────────── example/tests.py ──────────────────────────╮
    │ @@ -12,6 +12,6 @@                                                   │
    │                                                                     │
    │          assert snap == snapshot(                                   │
    │              [                                                      │
    │                  "SELECT ... FROM example_character",               │
    │ -                "SELECT ... FROM example_character LIMIT ...",     │
    │ +                "SELECT ... FROM example_character LEFT OUTER JOIN │
    │              ]                                                      │
    │          )                                                          │
    ╰─────────────────────────────────────────────────────────────────────╯
    Do you want to fix these snapshots? [y/n] (n):

Answer “y” to such prompts to automatically update snapshots in your test files:

.. code-block:: text

    Do you want to fix these snapshots? [y/n] (n): y
    ...
    ======================= short test summary info =======================
    ERROR example/tests.py::IndexTests::test_success - Failed: some snapshots in this test have incorrect values.
    ===================== 1 passed, 1 error in 0.60s ======================

inline-snapshot will directly modify your test file to update the snapshots, like:

.. code-block:: diff

            assert snap == snapshot(
                [
                    "SELECT ... FROM example_character",
    -                "SELECT ... FROM example_character LEFT OUTER JOIN example_class ON ... LIMIT ...",
    +                "SELECT ... FROM example_character LIMIT ...",
                ]
            )

Run the test again and it will pass:

.. code-block:: text

    $ pytest
    ...
    example/tests.py .                                              [100%]

    ========================== 1 passed in 0.05s ==========================

Update tests non-interactively
------------------------------

If you have a lot of tests to update, pressing “y” to each prompt can be tedious.
To avoid this, use ``--inline-snapshot=fix`` to apply `the “fix” category <https://15r10nk.github.io/inline-snapshot/latest/categories/#fix>`__, updating all failing snapshots:

.. code-block:: text

    $ pytest --inline-snapshot=fix
    ...
    example/tests.py .E                                             [100%]

    ═══════════════════════════ inline-snapshot ═══════════════════════════
    ──────────────────────────── Fix snapshots ────────────────────────────
    ╭───────────────────────── example/tests.py ──────────────────────────╮
    │ @@ -12,6 +12,6 @@                                                   │
    │                                                                     │
    │          assert snap == snapshot(                                   │
    │              [                                                      │
    │                  "SELECT ... FROM example_character",               │
    │ -                "SELECT ... FROM example_character LIMIT ...",     │
    │ +                "SELECT ... FROM example_character LEFT OUTER JOIN │
    │              ]                                                      │
    │          )                                                          │
    ╰─────────────────────────────────────────────────────────────────────╯
    These changes will be applied, because you used fix
    ...
    ======================= short test summary info =======================
    ERROR example/tests.py::IndexTests::test_success - Failed: some snapshots in this test have incorrect values.
    ===================== 1 passed, 1 error in 0.08s ======================

You can then review the changes with your source control tools, like ``git diff`` or a GUI tool.

Handle non-fingerprinted queries with dirty-equals
--------------------------------------------------

Sometimes queries are not fingerprinted, such as when they contain SQL that isn’t yet supported by the underlying SQL parsing Rust crate, `sqlparser <https://crates.io/crates/sqlparser>`__.
In such cases, do report an issue in `the sql-fingerprint repository <https://github.com/adamchainz/sql-fingerprint>`__.

But to write tests before any fix is available, you can use inline-snapshot’s `dirty-equals <https://dirty-equals.helpmanual.io/latest/>`__ support.
dirty-equals is a library for loosely comparing Python objects, and inline-snapshot integrates with it to allow you to use its values inside ``snapshot()`` calls.

For example, imagine you have a query that cannot be fingerprinted:

.. code-block:: python
    :emphasize-lines: 23

    from django.db import connection
    from django.db.transaction import atomic
    from django.db.utils import OperationalError
    from django.test import TestCase
    from inline_snapshot import snapshot
    from inline_snapshot_django import snapshot_queries


    class UnsupportedTests(TestCase):
        def test_success(self):
            with atomic(), snapshot_queries() as snap:
                with connection.cursor() as cursor:
                    try:
                        cursor.execute(
                            "SELECT imagine that this is some valid query "
                            "that cannot be parsed by sqlparser yet"
                        )
                    except OperationalError:
                        pass

            assert snap == snapshot(
                [
                    "SELECT imagine that this is some valid query that cannot be parsed by sqlparser yet"
                ]
            )

The recorded SQL will contain many details elided by fingerprinting, such as long lists of column names.
It may also include variable data, such as IDs or timestamps, making the test will fail on subsequent runs.

To fix such issues and provide a smaller fingerprint-like value, use |dirty-equals’ IsStr type|__ to partially match the fingerprinted SQL, like:

.. |dirty-equals’ IsStr type| replace:: dirty-equals’ ``IsStr`` type
__ https://dirty-equals.helpmanual.io/latest/types/string/#dirty_equals.IsStr

.. code-block:: python
    :emphasize-lines: 1, 24

    from dirty_equals import IsStr
    from django.db import connection
    from django.db.transaction import atomic
    from django.db.utils import OperationalError
    from django.test import TestCase
    from inline_snapshot import snapshot
    from inline_snapshot_django import snapshot_queries


    class UnsupportedTests(TestCase):
        def test_success(self):
            with atomic(), snapshot_queries() as snap:
                with connection.cursor() as cursor:
                    try:
                        cursor.execute(
                            "SELECT imagine that this is some valid query "
                            "that cannot be parsed by sqlparser yet"
                        )
                    except OperationalError:
                        pass

            assert snap == snapshot(
                [
                    IsStr(regex=r"SELECT .* some valid query .*"),
                ]
            )

This way, you can avoid matching irrelevant details while still ensuring that the query structure is approximately what’s expected.

If a fix becomes available for the fingerprinting issue, you can later update the test by removing the ``IsStr()`` call and rerunning tests with ``--inline-snapshot=fix``.
That should replace the ``IsStr()`` call with a proper fingerprint.
