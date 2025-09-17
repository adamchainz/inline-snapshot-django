Installation
============

Requirements
------------

Python 3.9 to 3.14 supported.

Django 4.2 to 6.0 supported.

Your test runner must be pytest, not Django's test framework, as inline-snapshot only supports pytest.

Installation
------------

With **pip**:

.. code-block:: sh

    python -m pip install inline-snapshot-django

There’s no need to add the package to your ``INSTALLED_APPS`` setting, as it does not act as a Django app.

You may wish to add `inline-snapshot configuration <https://15r10nk.github.io/inline-snapshot/latest/configuration/>`__ to your ``pyproject.toml`` file.
For example, if you use Ruff’s formatter, you may wish to select it in inline-snapshot’s ``format-command`` option, per the linked documentation.
