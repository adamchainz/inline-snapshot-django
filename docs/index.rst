inline-snapshot-django
======================

Extensions for using `inline-snapshot <https://github.com/15r10nk/inline-snapshot>`__ to test `Django <https://www.djangoproject.com/>`__ projects.

----

**Improve your Django and Git skills** with `my books <https://adamj.eu/books/>`__.

----

Welcome to the documentation for inline-snapshot-django.
This package provides tools for testing Django projects using inline-snapshot, a snapshot testing library that compares with and updates snapshots stored directly in your test functions.

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

inline-snapshot will automatically capture and update the contents of the ``snapshot()`` call within the test.
This allows you to quickly write and maintain tests that demonstrate the structure of your queries, like an advanced form of |Django’s assertNumQueries()|__.

.. |Django’s assertNumQueries()| replace:: Django’s ``assertNumQueries()``
__ https://docs.djangoproject.com/en/stable/topics/testing/tools/#django.test.TransactionTestCase.assertNumQueries

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   installation
   usage
   api
   changelog
   origins


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
