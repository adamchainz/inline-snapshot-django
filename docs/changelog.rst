=========
Changelog
=========

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
