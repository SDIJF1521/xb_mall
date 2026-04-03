"""
平台端邮件服务配置路由
- POST /manage_email_config          保存/更新邮件配置
- GET  /manage_email_config_select   查询当前配置
- POST /manage_email_config/verify   连通性测试
"""

from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter, Form, Depends, Header, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from data.redis_client import RedisClient, get_redis
from data.sql_client_pool import get_db_pool
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.data_mods import ManageEmailConfig

router = APIRouter()

PERM = "admin.email_config"


# ────────────────── 保存 / 更新 ──────────────────

@router.post("/manage_email_config")
async def manage_email_config(
    data: Annotated[ManageEmailConfig, Form()],
    db: Connection = Depends(get_db_pool),
    redis: RedisClient = Depends(get_redis),
    mongo: MongoDBClient = Depends(get_mongodb_client),
):
    try:
        ok, msg, _ = await verify_admin_with_permission(db, redis, data.token, required=PERM)
        if not ok:
            return {"current": False, "msg": msg}

        doc = {
            "sender_email": data.sender_email,
            "sender_password": data.sender_password,
            "smtp_server": data.smtp_server,
            "smtp_port": data.smtp_port,
            "use_ssl": data.use_ssl,
            "sender_name": data.sender_name,
        }

        existing = await mongo.find_one("EmailServiceConfig", {})
        if existing:
            await mongo.update_one("EmailServiceConfig", {}, {"$set": doc})
            return {"code": 200, "msg": "更新成功", "success": True}
        else:
            await mongo.insert_one("EmailServiceConfig", doc)
            return {"code": 200, "msg": "配置已创建", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────── 查询 ──────────────────

@router.get("/manage_email_config_select")
async def manage_email_config_select(
    db: Connection = Depends(get_db_pool),
    redis: RedisClient = Depends(get_redis),
    mongo: MongoDBClient = Depends(get_mongodb_client),
    access_token: str = Header(...),
):
    try:
        ok, msg, _ = await verify_admin_with_permission(db, redis, access_token, required=PERM)
        if not ok:
            return {"current": False, "msg": msg}

        doc = await mongo.find_one("EmailServiceConfig", {})
        if not doc:
            return {"code": 404, "msg": "配置不存在", "success": False}

        safe_doc = {
            "sender_email": doc.get("sender_email", ""),
            "smtp_server": doc.get("smtp_server", ""),
            "smtp_port": doc.get("smtp_port", 465),
            "use_ssl": doc.get("use_ssl", True),
            "sender_name": doc.get("sender_name", "系统通知"),
            "has_password": bool(doc.get("sender_password")),
        }
        return {"code": 200, "msg": "获取成功", "success": True, "data": safe_doc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────── 连通性测试 ──────────────────

@router.post("/manage_email_config/verify")
async def manage_email_config_verify(
    token: str = Form(...),
    db: Connection = Depends(get_db_pool),
    redis: RedisClient = Depends(get_redis),
    mongo: MongoDBClient = Depends(get_mongodb_client),
):
    try:
        ok, msg, _ = await verify_admin_with_permission(db, redis, token, required=PERM)
        if not ok:
            return {"current": False, "msg": msg}

        def get_verifier():
            from main import verifier
            return verifier

        v = get_verifier()
        return await v.verify_smtp_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
