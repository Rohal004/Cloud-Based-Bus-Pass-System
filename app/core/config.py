import os

class Settings:
    app_name: str = os.getenv("APP_NAME", "Cloud Bus Pass System")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./buspass.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    qr_code_secret: str = os.getenv("QR_CODE_SECRET", "local-qr-secret")

settings = Settings()
