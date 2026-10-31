import os

class Settings:
    PROJECT_NAME: str = "SAJAG — AI-Powered Industrial Safety Intelligence Platform"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sajag.db")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ]

settings = Settings()
