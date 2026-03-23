from typing import Optional, Tuple

import aiomysql

from data.sql_client import execute_db_query
from data.redis_client import RedisClient
from services.management_token_verify import ManagementTokenVerify
from services.manage_rbac import get_user_permissions, permission_match, permission_match_any


async def verify_admin_with_permission(
    db: aiomysql.Connection,
    redis: RedisClient,
    access_token: str,
    required: Optional[str] = None,
    required_any: Optional[list] = None,
) -> Tuple[bool, str, Optional[str]]:
    """校验平台 token 与权限。required 与 required_any 二选一；均无时仅校验登录。"""
    verify = ManagementTokenVerify(token=access_token, redis_client=redis)
    admin = await verify.token_admin()
    if not admin.get("current"):
        return False, admin.get("msg") or "验证失败", None
    username = admin.get("user")
    rows = await execute_db_query(db, "select user from manage_user where user = %s", (username,))
    v = await verify.run(rows)
    if not v.get("current"):
        return False, "验证失败", None
    perms = await get_user_permissions(db, username)
    if required and not permission_match(perms, required):
        return False, "无权操作", username
    if required_any and not permission_match_any(perms, required_any):
        return False, "无权操作", username
    return True, "ok", username
