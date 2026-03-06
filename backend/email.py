"""
Email service for login alerts using Gmail SMTP
"""
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Gmail SMTP configuration
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Gmail App Password


def _build_login_alert_html(
    username: str,
    timestamp: str,
    success: bool,
    ip_address: str
) -> str:
    """Build HTML email content for login alert"""
    status = "✅ Successful" if success else "❌ Failed"
    status_color = "#28a745" if success else "#dc3545"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #1a1a2e; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f8f9fa; padding: 20px; border: 1px solid #e9ecef; }}
            .detail {{ margin: 10px 0; padding: 10px; background: white; border-radius: 4px; }}
            .label {{ font-weight: bold; color: #495057; }}
            .status {{ color: {status_color}; font-weight: bold; }}
            .footer {{ text-align: center; padding: 15px; color: #6c757d; font-size: 12px; }}
            .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 4px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🔐 KeyAuth Login Alert</h2>
            </div>
            <div class="content">
                <p>A login attempt was detected on your account:</p>
                
                <div class="detail">
                    <span class="label">Account:</span> {username}
                </div>
                <div class="detail">
                    <span class="label">Status:</span> <span class="status">{status}</span>
                </div>
                <div class="detail">
                    <span class="label">Time:</span> {timestamp}
                </div>
                <div class="detail">
                    <span class="label">IP Address:</span> {ip_address}
                </div>
                
                <div class="warning">
                    <strong>⚠️ Wasn't you?</strong><br>
                    If you did not attempt this login, your password may be compromised. 
                    Please change your password immediately and review your account security.
                </div>
            </div>
            <div class="footer">
                This is an automated security alert from KeyAuth.
            </div>
        </div>
    </body>
    </html>
    """


async def send_login_alert(
    email: str,
    username: str,
    success: bool,
    ip_address: str = "Unknown"
) -> bool:
    """
    Send a login alert email to the user.
    
    Args:
        email: User's email address
        username: Username that attempted login
        success: Whether the login attempt was successful
        ip_address: IP address of the login attempt
        
    Returns:
        True if email sent successfully, False otherwise
    """
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    # Check if SMTP is configured
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"[EMAIL] SMTP not configured. Would send to {email}:")
        print(f"        User: {username}, Success: {success}, IP: {ip_address}, Time: {timestamp}")
        return False
    
    try:
        # Build email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🔐 Login Alert: {'Successful' if success else 'Failed'} login attempt"
        msg["From"] = SMTP_EMAIL
        msg["To"] = email
        
        # Plain text fallback
        plain_text = f"""
KeyAuth Login Alert

A login attempt was detected on your account:

Account: {username}
Status: {'Successful' if success else 'Failed'}
Time: {timestamp}
IP Address: {ip_address}

If this wasn't you, please change your password immediately.
"""
        
        # Attach both plain and HTML versions
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(_build_login_alert_html(username, timestamp, success, ip_address), "html"))
        
        # Send email via Gmail SMTP
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_EMAIL,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        
        print(f"[EMAIL] Login alert sent to {email} for user {username}")
        return True
        
    except Exception as e:
        print(f"[EMAIL] Failed to send email to {email}: {e}")
        return False


def _build_otp_html(username: str, code: str, expires_minutes: int) -> str:
    """Build HTML email content for OTP verification"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #1a1a2e; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f8f9fa; padding: 20px; border: 1px solid #e9ecef; }}
            .code-box {{ background: #1a1a2e; color: white; font-size: 32px; letter-spacing: 8px; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0; font-family: monospace; }}
            .footer {{ text-align: center; padding: 15px; color: #6c757d; font-size: 12px; }}
            .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 4px; margin-top: 15px; }}
            .info {{ color: #6c757d; font-size: 14px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🔐 KeyAuth Verification Code</h2>
            </div>
            <div class="content">
                <p>Hi <strong>{username}</strong>,</p>
                <p>Your keystroke pattern could not be verified. Use this one-time code to complete authentication:</p>
                
                <div class="code-box">{code}</div>
                
                <p class="info">This code expires in <strong>{expires_minutes} minutes</strong>.</p>
                
                <div class="warning">
                    <strong>⚠️ Security Notice</strong><br>
                    If you did not request this code, someone may be trying to access your account.
                    Please change your password immediately.
                </div>
            </div>
            <div class="footer">
                This is an automated security message from KeyAuth.
            </div>
        </div>
    </body>
    </html>
    """


async def send_otp_email(
    email: str,
    username: str,
    code: str,
    expires_minutes: int = 5
) -> bool:
    """
    Send OTP verification code email.
    
    Args:
        email: User's email address
        username: Username for personalization
        code: 6-digit OTP code
        expires_minutes: Minutes until code expires
        
    Returns:
        True if email sent successfully, False otherwise
    """
    # Check if SMTP is configured
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"[EMAIL] SMTP not configured. Would send OTP to {email}:")
        print(f"        User: {username}, Code: {code}")
        return False
    
    try:
        # Build email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🔐 KeyAuth Verification Code: {code}"
        msg["From"] = SMTP_EMAIL
        msg["To"] = email
        
        # Plain text fallback
        plain_text = f"""
KeyAuth Verification Code

Hi {username},

Your keystroke pattern could not be verified. Use this one-time code to complete authentication:

{code}

This code expires in {expires_minutes} minutes.

If you did not request this code, please change your password immediately.
"""
        
        # Attach both plain and HTML versions
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(_build_otp_html(username, code, expires_minutes), "html"))
        
        # Send email via Gmail SMTP
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_EMAIL,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        
        print(f"[EMAIL] OTP sent to {email} for user {username}")
        return True
        
    except Exception as e:
        print(f"[EMAIL] Failed to send OTP to {email}: {e}")
        return False
