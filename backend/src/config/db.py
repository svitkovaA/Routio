"""
file: db.py

Database configuration module.
"""

import os

# DB configuration
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_USER = os.getenv("POSTGRES_USER", "andrea")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
DB_DATABASE = os.getenv("POSTGRES_DB", "prediction")
PRODUCTION = os.getenv("PRODUCTION", "false").lower() == "true"
PRODUCTION_WINDOW_DAYS = 1

# End of file db.py
