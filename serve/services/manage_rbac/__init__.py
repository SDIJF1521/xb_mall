import json
from typing import Any, List, Optional, Tuple

import aiomysql

from data.sql_client import execute_db_query


def parse_permissions(raw: Any) -> List[str]:
    if raw is None:
        return ["*"]
    if isinstance(raw, (list, tuple)):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            return [str(x) for x in data] if isinstance(data, list) else ["*"]
        except json.JSONDecodeError:
            return ["*"]
    return ["*"]


def permission_match(perms: List[str], code: str) -> bool:
    if not perms:
        return False
    if "*" in perms:
        return True
    return code in perms


def permission_match_any(perms: List[str], codes: List[str]) -> bool:
    if not perms:
        return False
    if "*" in perms:
        return True
    return bool(set(perms) & set(codes))


async def get_user_permissions(db: aiomysql.Connection, username: str) -> List[str]:
    row = await execute_db_query(
        db,
        "SELECT r.permissions FROM manage_user u LEFT JOIN manage_role r ON u.role_id = r.id WHERE u.`user` = %s",
        (username,),
    )
    if not row:
        return ["*"]
    return parse_permissions(row[0][0])


async def get_user_role_row(db: aiomysql.Connection, username: str) -> Optional[Tuple[Any, ...]]:
    row = await execute_db_query(
        db,
        """SELECT u.role_id, r.name, r.description
           FROM manage_user u
           LEFT JOIN manage_role r ON u.role_id = r.id
           WHERE u.`user` = %s""",
        (username,),
    )
    return row[0] if row else None
