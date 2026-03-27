from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

from data.data_mods import FreezeMerchant
from data.redis_client import RedisClient,get_redis
from data.sql_client import get_db,execute_db_query

router = APIRouter()

@router.post("/manage_merchant_unfreeze")
async def thaw_merchant(
    data: Annotated[FreezeMerchant, Form()],
    db: Annotated[Connection, Depends(get_db)],
    redis: Annotated[RedisClient, Depends(get_redis)]
):
    """管理员解冻商户"""
    async def execute():
        sql_data = await execute_db_query(db,
                                          "SELECT * FROM mall_info WHERE user = %s AND mall_state = 2",
                                          (data.name,))
        if sql_data:
            await execute_db_query(db,
                                   "UPDATE mall_info SET mall_state = %s WHERE user = %s",
                                   (1,data.name))
            
            cache = CacheService(redis)
            await cache.delete_pattern(f'admin:merchant:*')
            await cache.delete_pattern(f'number:merchants')
            await cache.delete_pattern(f'admin:mall:info:*')
            
            return {"code":200,"msg":"解冻成功","success":True}
        else:
            return {"code":404,"msg":"用户不存在或未被冻结","success":False}
        
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, data.token, required="admin.user.merchant"
        )
        if not ok:
            return {"current": False, "msg": msg}
        return await execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))