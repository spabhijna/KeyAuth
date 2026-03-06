"""
OTP routes for 2FA fallback when keystroke verification fails
"""
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.email import send_otp_email
from backend.models import OTPSession, User
from backend.schemas import OTPRequest, OTPResponse, OTPVerifyRequest, OTPVerifyResponse

router = APIRouter(tags=["OTP Authentication"])

OTP_EXPIRY_MINUTES = 5
MAX_ATTEMPTS = 3


def generate_otp() -> str:
    """Generate a cryptographically secure 6-digit OTP"""
    return "".join(secrets.choice("0123456789") for _ in range(6))


@router.post(
    "/request-otp",
    response_model=OTPResponse,
    summary="Request OTP code",
    description="Request a one-time code for 2FA fallback authentication. Use when keystroke verification fails."
)
async def request_otp(data: OTPRequest, background_tasks: BackgroundTasks):
    """
    Request OTP for 2FA fallback.
    
    **When to use:**
    - After POST /verify returns "suspicious" status
    - User cannot authenticate via keystroke pattern
    
    **Flow:**
    1. Call this endpoint with user_id
    2. OTP sent to user's registered email
    3. User enters code via POST /verify-otp
    
    Previous unused OTPs for this user are invalidated.
    """
    user = await User.filter(id=data.user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.email:
        raise HTTPException(status_code=400, detail="User has no email registered")
    
    # Invalidate any existing unused OTPs for this user
    await OTPSession.filter(user=user, used=False).update(used=True)
    
    # Generate new OTP
    code = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)
    
    # Create OTP session
    await OTPSession.create(
        user=user,
        code=code,
        expires_at=expires_at,
        attempts=0,
        used=False
    )
    
    # Send OTP email in background
    background_tasks.add_task(
        send_otp_email,
        email=user.email,
        username=user.username,
        code=code,
        expires_minutes=OTP_EXPIRY_MINUTES
    )
    
    print(f"[OTP] Code generated for user {user.username}, expires at {expires_at}")
    
    return {
        "status": "otp_sent",
        "message": f"OTP sent to {user.email[:3]}***{user.email.split('@')[1]}",
        "expires_in_seconds": OTP_EXPIRY_MINUTES * 60
    }


@router.post(
    "/verify-otp",
    response_model=OTPVerifyResponse,
    summary="Verify OTP code",
    description="Verify the OTP code sent to user's email for 2FA authentication."
)
async def verify_otp(data: OTPVerifyRequest):
    """
    Verify OTP code for 2FA authentication.
    
    **Rules:**
    - Code expires after 5 minutes
    - Maximum 3 attempts per code
    - After 3 failed attempts, request a new OTP
    
    **Response statuses:**
    - **verified**: Authentication successful
    - **invalid**: Wrong code (attempts remaining)
    - **expired**: Code has expired
    - **max_attempts**: Too many wrong attempts
    """
    user = await User.filter(id=data.user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get the latest unused OTP for this user
    otp_session = await OTPSession.filter(
        user=user,
        used=False
    ).order_by("-created_at").first()
    
    if not otp_session:
        raise HTTPException(status_code=400, detail="No active OTP session. Request a new OTP.")
    
    # Check if expired - make both datetimes timezone-aware for comparison
    now = datetime.now(timezone.utc)
    expires = otp_session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    
    if now > expires:
        otp_session.used = True
        await otp_session.save()
        return {
            "status": "expired",
            "message": "OTP has expired. Please request a new code."
        }
    
    # Check max attempts
    if otp_session.attempts >= MAX_ATTEMPTS:
        otp_session.used = True
        await otp_session.save()
        return {
            "status": "max_attempts",
            "message": "Too many failed attempts. Please request a new code."
        }
    
    # Verify code
    if data.code != otp_session.code:
        otp_session.attempts += 1
        await otp_session.save()
        remaining = MAX_ATTEMPTS - otp_session.attempts
        
        if remaining == 0:
            otp_session.used = True
            await otp_session.save()
            return {
                "status": "max_attempts",
                "message": "Too many failed attempts. Please request a new code."
            }
        
        return {
            "status": "invalid",
            "message": f"Invalid code. {remaining} attempt(s) remaining."
        }
    
    # Success - mark OTP as used
    otp_session.used = True
    await otp_session.save()
    
    print(f"[OTP] Verified successfully for user {user.username}")
    
    return {
        "status": "verified",
        "message": "OTP verified successfully. Authentication complete."
    }
