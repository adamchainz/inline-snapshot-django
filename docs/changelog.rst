=========
Changelog
=========

Unreleased
----------

* Support Python 3.15.

* Switch package build backend from setuptools to `uv_build <https://docs.astral.sh/uv/concepts/build-backend/>`__.
  This makes builds with uv about nine times faster, since uv runs the backend natively, without creating a build environment or spawning a Python process.
  Additionally, source distributions no longer include test files, which setuptools previously included incompletely, missing the files needed to actually run them.

* Add Django 6.1 support.

* Drop Django 4.2 to 5.1 support.

1.4.0 (2026-02-12)
------------------

* Support dialect-specific SQL by passing ``dialect`` to sql-impressao.
  This fixes fingerprinting for some queries using dialect-specific SQL.

  `PR #42 <https://github.com/adamchainz/inline-snapshot-django/pull/42>`__.

* Drop Python 3.9 support.

1.3.0 (2025-09-18)
------------------

* Support Django 6.0.

1.2.0 (2025-09-09)
------------------

* Support Python 3.14.

1.1.0 (2025-06-04)
------------------

* Support capturing queries from multiple named database connections.

* Capture queries from all database connections by default.

1.0.0 (2025-06-03)
------------------

* Initial release.
