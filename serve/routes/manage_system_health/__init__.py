"""
系统健康检查路由
- GET /manage_system_health  检测 MySQL / Redis / MongoDB / SMTP 连通性
"""

import sys
import platform
import asyncio
import smtplib
import time
import logging

from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from data.redis_client import RedisClient, get_redis
from data.sql_client_pool import db_pool, get_db_pool
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()
logger = logging.getLogger(__name__)

PERM = "admin.system_settings"


async def _check_mysql() -> dict:
    try:
        t0 = time.perf_counter()
        rows = await db_pool.execute_query("SELECT 1")
        ms = round((time.perf_counter() - t0) * 1000, 1)
        if rows:
            return {"name": "MySQL", "ok": True, "msg": f"连接正常（{ms}ms）"}
        return {"name": "MySQL", "ok": False, "msg": "查询无结果"}
    except Exception as e:
        return {"name": "MySQL", "ok": False, "msg": str(e)}


async def _check_redis(redis: RedisClient) -> dict:
    try:
        t0 = time.perf_counter()
        await redis.setex("__health_check__", 5, "1")
        val = await redis.get("__health_check__")
        ms = round((time.perf_counter() - t0) * 1000, 1)
        if val == "1":
            return {"name": "Redis", "ok": True, "msg": f"连接正常（{ms}ms）"}
        return {"name": "Redis", "ok": False, "msg": "读写校验失败"}
    except Exception as e:
        return {"name": "Redis", "ok": False, "msg": str(e)}


async def _check_mongodb(mongo: MongoDBClient) -> dict:
    try:
        t0 = time.perf_counter()
        await mongo.find_one("__health_check__", {})
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return {"name": "MongoDB", "ok": True, "msg": f"连接正常（{ms}ms）"}
    except Exception as e:
        return {"name": "MongoDB", "ok": False, "msg": str(e)}


async def _check_smtp(mongo: MongoDBClient) -> dict:
    try:
        doc = await mongo.find_one("EmailServiceConfig", {})
        if not doc or not doc.get("smtp_server"):
            return {"name": "SMTP 邮件", "ok": False, "msg": "未配置邮件服务"}

        smtp_server = doc["smtp_server"]
        smtp_port = int(doc.get("smtp_port", 465))
        use_ssl = doc.get("use_ssl", True)
        sender_email = doc.get("sender_email", "")
        sender_password = doc.get("sender_password", "")

        def _test():
            t0 = time.perf_counter()
            server = None
            try:
                if use_ssl:
                    server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=8)
                else:
                    server = smtplib.SMTP(smtp_server, smtp_port, timeout=8)
                    server.starttls()
                server.login(sender_email, sender_password)
                ms = round((time.perf_counter() - t0) * 1000, 1)
                server.quit()
                return {"name": "SMTP 邮件", "ok": True, "msg": f"连接正常（{ms}ms）"}
            except smtplib.SMTPAuthenticationError:
                return {"name": "SMTP 邮件", "ok": False, "msg": "认证失败：授权码不正确"}
            except Exception as e:
                return {"name": "SMTP 邮件", "ok": False, "msg": str(e)}
            finally:
                if server:
                    try:
                        server.quit()
                    except Exception:
                        pass

        return await asyncio.to_thread(_test)
    except Exception as e:
        return {"name": "SMTP 邮件", "ok": False, "msg": str(e)}


@router.get("/manage_system_health")
async def manage_system_health(
    db: Connection = Depends(get_db_pool),
    redis: RedisClient = Depends(get_redis),
    mongo: MongoDBClient = Depends(get_mongodb_client),
    access_token: str = Header(...),
):
    try:
        ok, msg, _ = await verify_admin_with_permission(db, redis, access_token, required=PERM)
        if not ok:
            return {"current": False, "msg": msg}

        results = await asyncio.gather(
            _check_mysql(),
            _check_redis(redis),
            _check_mongodb(mongo),
            _check_smtp(mongo),
            return_exceptions=True,
        )

        checks = []
        for r in results:
            if isinstance(r, Exception):
                checks.append({"name": "未知", "ok": False, "msg": str(r)})
            else:
                checks.append(r)

        sys_info = {
            "python_version": sys.version.split()[0],
            "os": f"{platform.system()} {platform.release()}",
            "arch": platform.machine(),
        }

        return {
            "code": 200,
            "success": True,
            "data": {"checks": checks, "sys_info": sys_info},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
