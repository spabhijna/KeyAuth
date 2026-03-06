"""
Database connection setup - Phase 2
Configures Tortoise ORM with SQLite using FastAPI integration
"""

TORTOISE_ORM = {
    "connections": {"default": "sqlite://db.sqlite3"},
    "apps": {
        "models": {
            "models": ["backend.models"],
            "default_connection": "default",
        }
    },
}
