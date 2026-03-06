"""
Tortoise ORM models - Phase 2
Will contain User and TypingSample models
"""
from tortoise.models import Model
from tortoise import fields


class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=255, null=True)
    password_hash = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)


class TypingSample(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="samples")
    avg_hold_time = fields.FloatField()
    hold_time_std = fields.FloatField()
    avg_flight_time = fields.FloatField()
    flight_time_std = fields.FloatField()
    typing_speed = fields.FloatField()
    backspace_rate = fields.FloatField()
    created_at = fields.DatetimeField(auto_now_add=True)
