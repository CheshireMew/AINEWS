from typing import Optional

from ..infrastructure.database import transaction
from ..infrastructure.repositories import repositories
from ..core.exceptions import BusinessError, ValidationError
from .auth_service import AuthService


def update_credentials(current_username: str, current_password: str, new_username: Optional[str], new_password: Optional[str]):
    with transaction() as conn:
        repo_set = repositories(conn)
        auth_service = AuthService(repo_set.config)
        if auth_service.is_environment_managed():
            raise BusinessError('当前管理员账号由环境变量管理，不能在后台修改')
        current_ok = auth_service.authenticate_user(current_username, current_password)
        if not current_ok:
            raise BusinessError('当前密码错误')
        if new_username:
            if len(new_username) < 3:
                raise ValidationError('用户名长度至少为3个字符')
            repo_set.config.set_config('admin_username', new_username)
        if new_password:
            if len(new_password) < 6:
                raise ValidationError('密码长度至少为6个字符')
            repo_set.config.set_config('admin_password', new_password)
        return {'message': '账户信息已更新'}
