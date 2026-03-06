from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from backend.routes import auth_routes, typing_routes
from backend.database import TORTOISE_ORM


app = FastAPI(
    title="KeyAuth - Keystroke Authentication API",
    description="""
## Behavioral Biometric Authentication System

This API implements **keystroke dynamics authentication** using Isolation Forest ML models.

### Authentication Flow

1. **Register** → `POST /register`
2. **Train Model** → User types phrase 8-10 times → `POST /train`
3. **Login** → `POST /login` (password verification)
4. **Verify Typing** → User types phrase → `POST /verify` (behavioral verification)

### Keystroke Event Format

Each keystroke is captured as:
```json
{"key": "a", "type": "down", "time": 0}   // key pressed at time 0ms
{"key": "a", "type": "up", "time": 90}    // key released at 90ms
```

The system extracts features like:
- Average hold time
- Flight time between keys
- Typing speed
- Backspace rate
""",
    version="1.0.0",
    contact={
        "name": "KeyAuth Support"
    },
    license_info={
        "name": "MIT"
    }
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True
)

app.include_router(auth_routes.router)
app.include_router(typing_routes.router)


@app.get("/")
def root():
    return {"message": "Backend is running"}
