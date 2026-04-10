from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Protocol

import jwt
from pydantic import BaseModel

from ..core.config import settings
from ..core.exceptions import ConfigurationError

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

class Token(BaseModel):
    access_token: str
    token_type: str


class ConfigStore(Protocol):
    def get_config(self, key: str) -> Optional[str]:
        ...

    def set_config(self, key: str, value: str):
        ...


@dataclass(frozen=True)
class AdminCredentials:
    source: str
    username: str
    password: str


class AuthService:
    def __init__(self, config_repo: ConfigStore):
        self.config_repo = config_repo
        self.secret_key = self._get_or_create_secret_key()

    def _get_or_create_secret_key(self) -> str:
        if settings.JWT_SECRET_KEY:
            return settings.JWT_SECRET_KEY
            
        import secrets
        key = self.config_repo.get_config("jwt_secret_key")
        if not key:
            key = secrets.token_urlsafe(32)
            self.config_repo.set_config("jwt_secret_key", key)
        return key

    @staticmethod
    def _normalize_credentials(source: str, username: str | None, password: str | None) -> AdminCredentials | None:
        normalized_username = (username or "").strip()
        normalized_password = (password or "").strip()
        if not normalized_username and not normalized_password:
            return None
        if not normalized_username or not normalized_password:
            raise ConfigurationError(f"{source} 管理员账号配置不完整")
        return AdminCredentials(source=source, username=normalized_username, password=normalized_password)

    def get_admin_credentials(self) -> AdminCredentials:
        env_credentials = self._normalize_credentials("环境变量", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD)
        if env_credentials:
            return env_credentials

        db_credentials = self._normalize_credentials(
            "数据库",
            self.config_repo.get_config("admin_username"),
            self.config_repo.get_config("admin_password"),
        )
        if db_credentials:
            return db_credentials

        raise ConfigurationError("管理员账号未配置，请先设置环境变量或后台配置")

    def is_environment_managed(self) -> bool:
        return self._normalize_credentials("环境变量", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD) is not None

    def authenticate_user(self, username: str, password: str) -> bool:
        credentials = self.get_admin_credentials()
        return username == credentials.username and password == credentials.password

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            return username
        except jwt.PyJWTError:
            return None
