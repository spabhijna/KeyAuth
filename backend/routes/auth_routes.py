from fastapi import APIRouter, HTTPException
from backend.models import User
from backend.auth import hash_password, verify_password
from backend.schemas import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="Register a new user",
    description="Create a new user account. After registration, use POST /train to train the user's typing model."
)
async def register(data: RegisterRequest):
    """
    Register a new user with username and password.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Optional email address
    - **password**: Password (minimum 6 characters)
    
    Returns the created user ID.
    """
    print(f"[REGISTER] Attempt: {data.username}")
    existing = await User.filter(username=data.username).first()

    if existing:
        print(f"[REGISTER] Failed: User {data.username} already exists")
        raise HTTPException(status_code=400, detail="User already exists")

    user = await User.create(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password)
    )

    print(f"[REGISTER] Success: User {data.username} created with ID {user.id}")
    return {
        "message": "User created",
        "user_id": user.id
    }


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login with password",
    description="Verify username and password. After successful login, user must complete keystroke verification via POST /verify."
)
async def login(data: LoginRequest):
    """
    Authenticate user with username and password.
    
    - **username**: Registered username
    - **password**: User's password
    
    Returns user_id if password is correct. 
    Next step: Send keystrokes to POST /verify for behavioral verification.
    """
    print(f"[LOGIN] Attempt: {data.username}")
    user = await User.filter(username=data.username).first()

    if not user:
        print(f"[LOGIN] Failed: User {data.username} not found")
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.password, user.password_hash):
        print(f"[LOGIN] Failed: Invalid password for {data.username}")
        raise HTTPException(status_code=401, detail="Invalid password")

    print(f"[LOGIN] Success: {data.username} (ID: {user.id})")
    return {
        "status": "password_verified",
        "user_id": user.id
    }
