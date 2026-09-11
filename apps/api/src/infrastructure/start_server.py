"""Migrate before importing the app; stop deployment if migration fails."""
import os
import subprocess
import sys


def main():
    if os.getenv("APP_ENV") == "production":
        if not os.getenv("DATABASE_URL", "").startswith("postgresql+psycopg://"):
            raise RuntimeError("Production requires a PostgreSQL DATABASE_URL using psycopg")
        if len(os.getenv("JWT_SECRET", "")) < 32:
            raise RuntimeError("Production requires a dedicated JWT_SECRET of at least 32 characters")
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    os.execv(sys.executable, [sys.executable, "-m", "uvicorn", "src.main:app",
                            "--host", "0.0.0.0", "--port", os.getenv("PORT", "8000")])


if __name__ == "__main__":
    main()
