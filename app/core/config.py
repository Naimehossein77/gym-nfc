# app/core/config.py
import os
from typing import Optional
from dotenv import load_dotenv   # 👈
load_dotenv()                    # 👈 ensure .env is loaded no matter who imports settings

class Settings:
    def __init__(self):
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

        self.app_name = os.getenv("APP_NAME", "Gym NFC Management System")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"

        self.nfc_reader_timeout = int(os.getenv("NFC_READER_TIMEOUT", "30"))
        self.nfc_write_timeout = int(os.getenv("NFC_WRITE_TIMEOUT", "10"))

        # 👇 Encrypted NFC payload key
        self.fernet_key: Optional[str] = os.getenv("FERNET_KEY")

settings = Settings()
