import os
from typing import Optional


class Settings:
    """Application settings"""
    
    def __init__(self):
        # JWT Settings
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
        
        # Application Settings
        self.app_name = os.getenv("APP_NAME", "Gym NFC Management System")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        
        # NFC Reader Settings
        self.nfc_reader_timeout = int(os.getenv("NFC_READER_TIMEOUT", "30"))
        self.nfc_write_timeout = int(os.getenv("NFC_WRITE_TIMEOUT", "10"))


# Global settings instance
settings = Settings()