"""
平台基础配置路由
- POST /manage_platform_config        保存/更新平台基础配置
- GET  /manage_platform_config_select  查询当前配置（需鉴权）
- GET  /platform_info                  公开接口，前端展示用
"""

from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter, Form, Depends, Header, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from data.redis_client import RedisClient, get_redis
from data.sql_client_pool import get_db_pool
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()

PERM = "admin.system_settings"


@router.post("/manage_platform_config")
async def manage_platform_config(
    token: str = Form(...),
    platform_name: str = Form(""),
    platform_desc: str = Form(""),
    contact_email: str = Form(""),
    contact_phone: str = Form(""),
    icp_number: str = Form(""),
    copyright_text: str = Form(""),
    db: Connection = Depends(get_db_pool),
    redis: RedisClient = Depends(get_redis),
    mongo: MongoDBClient = Depends(get_mongodb_client),
):
    try:
        ok, msg, _ = await verify_admin_with_permission(db, redis, token, required=PERM)
        if not ok:
            return {"current": False, "msg": msg}

        doc = {
            "platform_name": platform_name,
            "platform_desc": platform_desc,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "icp_number": icp_number,
            "copyright_text": copyright_text,
        }

        existing = await mongo.find_one("PlatformConfig", {})
        if existing:
            await mongo.update_one("PlatformConfig", {}, {"$set": doc})
            return {"code": 200, "msg": "更新成功", "success": True}
        else:
            await mongo.insert_one("PlatformConfig", doc)
            return {"code": 200, "msg": "配置已创建", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/manage_platform_config_select")
async def manage_platform_config_select(
    db: Connection = Depends(get_db_pool),
    redis: RedisClient = Depends(get_redis),
    mongo: MongoDBClient = Depends(get_mongodb_client),
    access_token: str = Header(...),
):
    try:
        ok, msg, _ = await verify_admin_with_permission(db, redis, access_token, required=PERM)
        if not ok:
            return {"current": False, "msg": msg}

        doc = await mongo.find_one("PlatformConfig", {})
        if not doc:
            return {"code": 200, "msg": "暂无配置", "success": True, "data": None}

        return {
            "code": 200,
            "msg": "获取成功",
            "success": True,
            "data": {
                "platform_name": doc.get("platform_name", ""),
                "platform_desc": doc.get("platform_desc", ""),
                "contact_email": doc.get("contact_email", ""),
                "contact_phone": doc.get("contact_phone", ""),
                "icp_number": doc.get("icp_number", ""),
                "copyright_text": doc.get("copyright_text", ""),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platform_info")
async def platform_info(
    mongo: MongoDBClient = Depends(get_mongodb_client),
):
    """公开接口：返回平台展示信息，无需登录。"""
    try:
        doc = await mongo.find_one("PlatformConfig", {})
        defaults = {
            "platform_name": "xb商城",
            "copyright_text": "版权所有 © xb商城，保留所有权利。",
            "icp_number": "",
            "contact_email": "",
            "contact_phone": "",
        }
        if not doc:
            return {"success": True, "data": defaults}
        return {
            "success": True,
            "data": {
                k: doc.get(k) or v for k, v in defaults.items()
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
