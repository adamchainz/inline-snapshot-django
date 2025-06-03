from django.db import models

class Character(models.Model):
    name = models.TextField()
    strength = models.IntegerField()
    charisma = models.IntegerField()
