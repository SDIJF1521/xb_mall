from aiomysql import Connection
from fastapi import APIRouter,Depends,Header,HTTPException

from services.logistics import LogisticsService
from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

from data.redis_client import RedisClient, get_redis
from data.sql_client_pool import db_pool,get_db_pool
from data.mongodb_client import MongoDBClient,get_mongodb_client

router = APIRouter()
@router.get("/manage_logistics_config_select")
async def manage_logistics_config_select(
                                db:Connection=Depends(get_db_pool),
                                redis:RedisClient=Depends(get_redis),
                                mongo:MongoDBClient=Depends(get_mongodb_client),
                                access_token: str=Header(...)
                                ):

    async def execute():
        Logistics = LogisticsService(db_pool,mongo,redis)
        return await Logistics.get_config()
        
    try:
        ok, msg, _ = await verify_admin_with_permission(
                db, redis, access_token, required="admin.logistics_config"
            )
        if not ok:
            return {"current": False, "msg": msg}
        return await execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))