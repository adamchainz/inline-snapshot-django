from __future__ import annotations

SECRET_KEY = "NOTASECRET"

ALLOWED_HOSTS: list[str] = []

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "other": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": True,
    },
    "other": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": True,
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "tests",
]

MIDDLEWARE: list[str] = []

USE_TZ = True
