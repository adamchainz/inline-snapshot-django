from __future__ import annotations

from typing import Any

from django.db import models


class Character(models.Model):
    name: Any = models.TextField()
    strength: Any = models.IntegerField()
    charisma: Any = models.IntegerField()
