from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from backend.models import User, TypingSample
from backend.auth import hash_password, verify_password
from backend.email import send_login_alert
from backend.schemas import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse
from backend.ml.feature_extractor import extract_features
from backend.ml.train_model import train_model

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="Register a new user",
    description="Create a new user account with typing samples. Model is trained automatically."
)
async def register(data: RegisterRequest):
    """
    Register a new user with username, password, and typing samples.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Email address for login alerts
    - **password**: Password (minimum 6 characters)
    - **samples**: 20+ typing samples for model training
    
    Returns the created user ID. Model is trained immediately.
    """
    print(f"[REGISTER] Attempt: {data.username}")
    existing = await User.filter(username=data.username).first()

    if existing:
        print(f"[REGISTER] Failed: User {data.username} already exists")
        raise HTTPException(status_code=400, detail="User already exists")

    if len(data.samples) < 20:
        raise HTTPException(status_code=400, detail="At least 20 typing samples required")

    # Create user
    user = await User.create(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password)
    )

    # Extract features and store samples
    feature_vectors = []
    for keystrokes in data.samples:
        features = extract_features(keystrokes)
        feature_vectors.append(features)
        
        # Store sample in database
        await TypingSample.create(
            user=user,
            mean_hold=features[0],
            std_hold=features[1],
            mean_flight=features[2],
            std_flight=features[3],
            hold_0=features[4],
            hold_1=features[5],
            hold_2=features[6],
            hold_3=features[7],
            hold_4=features[8],
            hold_5=features[9],
            flight_0=features[10],
            flight_1=features[11],
            flight_2=features[12],
            flight_3=features[13],
            flight_4=features[14],
            flight_5=features[15],
        )

    # Train model
    train_model(feature_vectors, user.id)

    print(f"[REGISTER] Success: User {data.username} created with ID {user.id}, model trained with {len(feature_vectors)} samples")
    return {
        "message": "User created and model trained",
        "user_id": user.id
    }


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login with password",
    description="Verify username and password. After successful login, user must complete keystroke verification via POST /verify."
)
async def login(data: LoginRequest, request: Request, background_tasks: BackgroundTasks):
    """
    Authenticate user with username and password.
    
    - **username**: Registered username
    - **password**: User's password
    
    Returns user_id if password is correct. 
    Next step: Send keystrokes to POST /verify for behavioral verification.
    """
    print(f"[LOGIN] Attempt: {data.username}")
    user = await User.filter(username=data.username).first()
    
    # Get client IP address
    client_ip = request.client.host if request.client else "Unknown"

    if not user:
        print(f"[LOGIN] Failed: User {data.username} not found")
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.password, user.password_hash):
        print(f"[LOGIN] Failed: Invalid password for {data.username}")
        # Send failed login alert email
        if user.email:
            background_tasks.add_task(
                send_login_alert,
                email=user.email,
                username=user.username,
                success=False,
                ip_address=client_ip
            )
        raise HTTPException(status_code=401, detail="Invalid password")

    print(f"[LOGIN] Success: {data.username} (ID: {user.id})")
    # Send successful login alert email
    if user.email:
        background_tasks.add_task(
            send_login_alert,
            email=user.email,
            username=user.username,
            success=True,
            ip_address=client_ip
        )
    return {
        "status": "password_verified",
        "user_id": user.id
    }
