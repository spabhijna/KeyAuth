"""
Tortoise ORM models - Phase 2
Will contain User and TypingSample models
"""
from tortoise.models import Model
from tortoise import fields


class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=255)
    password_hash = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)


class TypingSample(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="samples")
    # Hold time features
    mean_hold = fields.FloatField()
    std_hold = fields.FloatField()
    median_hold = fields.FloatField()
    min_hold = fields.FloatField()
    max_hold = fields.FloatField()
    # Flight time features
    mean_flight = fields.FloatField()
    std_flight = fields.FloatField()
    median_flight = fields.FloatField()
    # Timing features
    typing_speed = fields.FloatField()
    total_time = fields.FloatField()
    duration_per_char = fields.FloatField()
    backspace_rate = fields.FloatField()
    created_at = fields.DatetimeField(auto_now_add=True)


class OTPSession(Model):
    """OTP session for 2FA fallback when keystroke verification fails"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="otp_sessions")
    code = fields.CharField(max_length=6)  # 6-digit code
    expires_at = fields.DatetimeField()
    attempts = fields.IntField(default=0)  # Max 3 attempts
    used = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
