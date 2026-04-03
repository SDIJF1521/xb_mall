from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Form,Depends,HTTPException

from services.logistics import LogisticsService
from services.manage_admin_guard import verify_admin_with_permission


from data.redis_client import RedisClient, get_redis
from data.sql_client_pool import db_pool,get_db_pool
from data.mongodb_client import MongoDBClient,get_mongodb_client
from data.data_mods import ManageLogisticsConfig


# ────────────────── 物流配置 ──────────────────
router = APIRouter()
@router.post('/manage_logistics_config')
async def manage_logistics_config(
                                data:Annotated[ManageLogisticsConfig,Form()],
                                db:Connection=Depends(get_db_pool),
                                redis:RedisClient=Depends(get_redis),
                                mongo:MongoDBClient=Depends(get_mongodb_client),
                                ):

    async def execute():
        Logistics = LogisticsService(db_pool,mongo,redis)
        return await Logistics.config(data.user_code,data.verification_code,data.production_environment)
        

        
    try:
        ok, msg, _ = await verify_admin_with_permission(
                db, redis, data.token, required="admin.logistics_config"
            )
        if not ok:
            return {"current": False, "msg": msg}
        return await execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/manage_logistics_config/verify')
async def manage_logistics_config_verify(
        token: str = Form(...),
        db: Connection = Depends(get_db_pool),
        redis: RedisClient = Depends(get_redis),
        mongo: MongoDBClient = Depends(get_mongodb_client),
):
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, token, required="admin.logistics_config"
        )
        if not ok:
            return {"current": False, "msg": msg}

        logistics = LogisticsService(db_pool, mongo, redis)
        return await logistics.verify_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

