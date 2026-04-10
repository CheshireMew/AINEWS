from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel

from ..core.exceptions import AuthenticationError
from ..core.response import APIResponse
from ..infrastructure.repositories import repositories
from ..services.auth_service import AuthService
from ..services.auth_management import update_credentials as update_credentials_service

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


class CredentialsUpdate(BaseModel):
    current_password: str
    new_username: str | None = None
    new_password: str | None = None


def get_auth_service():
    return AuthService(repositories().config)


async def get_current_user(token: str = Depends(oauth2_scheme), auth_service: AuthService = Depends(get_auth_service)):
    username = auth_service.verify_token(token)
    if username is None:
        raise AuthenticationError(
            "登录状态已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), auth_service: AuthService = Depends(get_auth_service)):
    if not auth_service.authenticate_user(form_data.username, form_data.password):
        raise AuthenticationError(
            "用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(data={"sub": form_data.username})
    return APIResponse.success(data={"access_token": access_token, "token_type": "bearer"}, message="登录成功")


@router.post("/system/credentials")
def update_credentials(req: CredentialsUpdate, user: str = Depends(get_current_user)):
    result = update_credentials_service(user, req.current_password, req.new_username, req.new_password)
    return APIResponse.success(message=result["message"])
