
import os
from typing import List
from dotenv import load_dotenv

# Load env variables
env_file = '.env.production' if os.getenv('ENV') == 'production' else '.env.development'
load_dotenv(env_file)

class Settings:
    PROJECT_NAME: str = "AINews Admin API"
    ENV: str = os.getenv('ENV', 'development')
    
    # CORS
    ALLOWED_ORIGINS_STR: str = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173')
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS_STR.split(',')]

    # Auth
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', '')
    ADMIN_USERNAME: str = os.getenv('ADMIN_USERNAME', '')
    ADMIN_PASSWORD: str = os.getenv('ADMIN_PASSWORD', '')

    # AI & 3rd Party
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID', '')
    DEEPSEEK_API_KEY: str = os.getenv('DEEPSEEK_API_KEY', '')

settings = Settings()
