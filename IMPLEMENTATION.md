# KeyAuth - Implementation Status

Keystroke-based behavioral biometric authentication system.

---

## Project Structure

```
KeyAuth/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Tortoise ORM configuration
│   ├── models.py            # User and TypingSample ORM models
│   ├── schemas.py           # Pydantic schemas (placeholder)
│   ├── auth.py              # Password hashing utilities
│   ├── routes/
│   │   ├── auth_routes.py   # /register, /login endpoints
│   │   └── typing_routes.py # /verify endpoint
│   └── ml/
│       ├── feature_extractor.py  # Keystroke feature extraction
│       └── predict.py            # User verification (placeholder)
├── db.sqlite3               # SQLite database
├── pyproject.toml           # Dependencies
└── Schema.md                # Feature vector specification
```

---

## Completed Phases

### Phase 1 — Project Setup ✅
- FastAPI application initialized
- Project structure created
- Dependencies configured via `pyproject.toml`

### Phase 2 — Database Setup ✅
- **Tortoise ORM** + **SQLite** integration
- Auto-generated database schemas
- Two ORM models:
  - `User` — stores credentials
  - `TypingSample` — stores typing behavior features

### Phase 3 — Authentication System ✅
- Password hashing with **bcrypt**
- User registration and login endpoints
- Error handling for duplicates and invalid credentials

### Phase 4 — Typing Verification API ✅
- Keystroke feature extraction pipeline
- `/verify` endpoint for behavioral verification
- Typing samples saved on successful verification
- Placeholder ML prediction (returns mock confidence)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/register` | Create new user |
| POST | `/login` | Verify password credentials |
| POST | `/verify` | Verify typing behavior |

---

## API Reference

### POST /register

Create a new user account.

**Request:**
```json
{
  "username": "user1",
  "password": "pass123"
}
```

**Response (201):**
```json
{
  "message": "User created",
  "user_id": 1
}
```

**Errors:**
- `400` — User already exists

---

### POST /login

Verify user credentials.

**Request:**
```json
{
  "username": "user1",
  "password": "pass123"
}
```

**Response (200):**
```json
{
  "status": "password_verified",
  "user_id": 1
}
```

**Errors:**
- `404` — User not found
- `401` — Invalid password

---

### POST /verify

Verify typing behavior against user profile.

**Request:**
```json
{
  "user_id": 1,
  "keystrokes": [
    {"key": "a", "type": "down", "time": 0},
    {"key": "a", "type": "up", "time": 100},
    {"key": "b", "type": "down", "time": 150},
    {"key": "b", "type": "up", "time": 250}
  ]
}
```

**Response (200):**
```json
{
  "status": "verified",
  "confidence": 0.85
}
```

**Status values:**
- `verified` — typing pattern matches (prediction = 1)
- `suspicious` — anomaly detected (prediction = -1)

**Errors:**
- `404` — User not found

---

## Database Schema

### User Table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| username | VARCHAR(50) | Unique username |
| password_hash | VARCHAR(255) | bcrypt hash |
| created_at | TIMESTAMP | Account creation time |

### TypingSample Table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | Foreign key to User |
| avg_hold_time | FLOAT | Average key hold duration (ms) |
| hold_time_std | FLOAT | Standard deviation of hold time |
| avg_flight_time | FLOAT | Average time between keys (ms) |
| flight_time_std | FLOAT | Standard deviation of flight time |
| typing_speed | FLOAT | Keys per second |
| backspace_rate | FLOAT | Ratio of backspaces to total keys |
| created_at | TIMESTAMP | Sample collection time |

---

## Feature Vector

As defined in `Schema.md`:

```python
feature_vector = [
    avg_hold_time,    # Average key press duration
    hold_time_std,    # Variation in hold times
    avg_flight_time,  # Average gap between keystrokes
    flight_time_std,  # Variation in flight times
    typing_speed,     # Characters per second
    backspace_rate    # Error correction frequency
]
```

Example: `[101, 3.2, 74, 4.5, 5.3, 0.02]`

---

## Dependencies

```toml
aiosqlite>=0.22.1      # SQLite async driver
bcrypt>=4.0.0          # Password hashing
fastapi>=0.135.1       # Web framework
joblib>=1.5.3          # Model serialization
scikit-learn>=1.8.0    # ML (One-Class SVM)
tortoise-orm>=1.1.6    # Async ORM
uvicorn>=0.41.0        # ASGI server
```

---

## Running the Server

```bash
# Install dependencies
uv sync

# Start server
uvicorn backend.main:app --reload

# Access
http://127.0.0.1:8000       # API root
http://127.0.0.1:8000/docs  # Swagger UI
```

---

## Architecture

```
Frontend (typing capture)
        ↓
FastAPI Backend
        ↓
Authentication (/register, /login)
        ↓
Typing Verification (/verify)
        ↓
Feature Extraction (ml/feature_extractor.py)
        ↓
One-Class SVM Prediction (ml/predict.py)
        ↓
Tortoise ORM
        ↓
SQLite Database
```

---

## TODO — Remaining Phases

### Phase 5 — Registration Training
- Collect 20 typing samples during registration
- Train per-user One-Class SVM model
- Save model to disk with joblib

### Phase 6 — Real ML Integration
- Replace placeholder prediction with trained model
- Load user-specific model during verification
- Implement model retraining on successful logins

### Phase 7 — Frontend Integration
- JavaScript keystroke capture
- Real-time timing collection
- API integration with /verify endpoint
