import os

# DB configuration
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_USER = os.getenv("POSTGRES_USER", "andrea")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
DB_DATABASE = os.getenv("POSTGRES_DB", "prediction")