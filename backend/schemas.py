"""
Pydantic schemas for API request/response validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional


# ============== Auth Schemas ==============

class RegisterRequest(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email for login alerts")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "johndoe",
                    "email": "john@example.com",
                    "password": "securepassword123"
                }
            ]
        }
    }


class RegisterResponse(BaseModel):
    """User registration response"""
    message: str = Field(description="Success message")
    user_id: int = Field(description="Created user ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "User created",
                    "user_id": 1
                }
            ]
        }
    }


class LoginRequest(BaseModel):
    """User login request"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "johndoe",
                    "password": "securepassword123"
                }
            ]
        }
    }


class LoginResponse(BaseModel):
    """User login response"""
    status: str = Field(description="Login status")
    user_id: int = Field(description="Authenticated user ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "password_verified",
                    "user_id": 1
                }
            ]
        }
    }


# ============== Typing Schemas ==============

class KeystrokeEvent(BaseModel):
    """Single keystroke event"""
    key: str = Field(..., description="Key pressed (e.g., 'a', 'Backspace')")
    type: Literal["down", "up"] = Field(..., description="Event type: 'down' or 'up'")
    time: int = Field(..., ge=0, description="Timestamp in milliseconds")


class PhraseResponse(BaseModel):
    """Random phrase for typing"""
    phrase: str = Field(description="Phrase to type for training/verification")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "phrase": "The quick brown fox jumps over the lazy dog"
                }
            ]
        }
    }


class TrainRequest(BaseModel):
    """Training request with multiple typing samples"""
    user_id: int = Field(..., description="User ID to train model for")
    samples: list[list[dict]] = Field(
        ..., 
        min_length=8,
        description="List of 8-10 typing sessions. Each session is a list of keystroke events."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 1,
                    "samples": [
                        [
                            {"key": "t", "type": "down", "time": 0},
                            {"key": "t", "type": "up", "time": 90},
                            {"key": "h", "type": "down", "time": 150},
                            {"key": "h", "type": "up", "time": 230},
                            {"key": "e", "type": "down", "time": 300},
                            {"key": "e", "type": "up", "time": 380}
                        ],
                        [
                            {"key": "t", "type": "down", "time": 0},
                            {"key": "t", "type": "up", "time": 85},
                            {"key": "h", "type": "down", "time": 140},
                            {"key": "h", "type": "up", "time": 220},
                            {"key": "e", "type": "down", "time": 290},
                            {"key": "e", "type": "up", "time": 370}
                        ],
                        "... (10 samples required)"
                    ]
                }
            ]
        }
    }


class TrainResponse(BaseModel):
    """Training completion response"""
    status: str = Field(description="Training status")
    samples_used: int = Field(description="Number of samples used for training")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "training_complete",
                    "samples_used": 10
                }
            ]
        }
    }


class VerifyRequest(BaseModel):
    """Keystroke verification request"""
    user_id: int = Field(..., description="User ID to verify against")
    keystrokes: list[dict] = Field(
        ...,
        description="List of keystroke events from a single typing session"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 1,
                    "keystrokes": [
                        {"key": "t", "type": "down", "time": 0},
                        {"key": "t", "type": "up", "time": 90},
                        {"key": "h", "type": "down", "time": 150},
                        {"key": "h", "type": "up", "time": 230},
                        {"key": "e", "type": "down", "time": 300},
                        {"key": "e", "type": "up", "time": 380}
                    ]
                }
            ]
        }
    }


class VerifyResponse(BaseModel):
    """Verification result"""
    status: Literal["verified", "suspicious"] = Field(description="Verification result")
    confidence: float = Field(ge=0, le=1, description="Confidence score (0.0 to 1.0)")
    fallback_available: bool = Field(default=False, description="Whether OTP fallback is available")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "verified",
                    "confidence": 0.87,
                    "fallback_available": False
                }
            ]
        }
    }


# ============== OTP Schemas ==============

class OTPRequest(BaseModel):
    """Request OTP for 2FA fallback"""
    user_id: int = Field(..., description="User ID to send OTP to")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 1
                }
            ]
        }
    }


class OTPVerifyRequest(BaseModel):
    """Verify OTP code"""
    user_id: int = Field(..., description="User ID")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 1,
                    "code": "123456"
                }
            ]
        }
    }


class OTPResponse(BaseModel):
    """OTP request response"""
    status: str = Field(description="OTP status")
    message: str = Field(description="Status message")
    expires_in_seconds: Optional[int] = Field(default=None, description="Seconds until OTP expires")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "otp_sent",
                    "message": "OTP sent to email",
                    "expires_in_seconds": 300
                }
            ]
        }
    }


class OTPVerifyResponse(BaseModel):
    """OTP verification response"""
    status: Literal["verified", "invalid", "expired", "max_attempts"] = Field(description="Verification result")
    message: str = Field(description="Status message")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "verified",
                    "message": "OTP verified successfully"
                }
            ]
        }
    }
