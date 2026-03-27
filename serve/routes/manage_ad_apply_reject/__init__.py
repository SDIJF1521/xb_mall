from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.data_mods import ManageAdApplyReject

router = APIRouter()


@router.post('/manage_ad_apply_reject')
async def manage_ad_apply_reject(
    body: ManageAdApplyReject,
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """平台端：驳回广告投放申请"""
    try:
        ok, msg, username = await verify_admin_with_permission(
            db, redis, access_token, required="admin.system_settings"
        )
        if not ok:
            return {"current": False, "msg": msg}

        row = await execute_db_query(
            db,
            "SELECT id, mall_id, shopping_id, title, status FROM ad_apply WHERE id = %s",
            (body.apply_id,)
        )
        if not row:
            return {"current": False, "msg": "申请不存在"}
        apply = row[0]
        if apply[4] != 'pending':
            return {"current": False, "msg": "该申请已处理"}

        now = datetime.now()
        await execute_db_query(
            db,
            "UPDATE ad_apply SET status='rejected', reject_reason=%s, review_time=%s, reviewer=%s WHERE id=%s",
            (body.reason, now, username, body.apply_id)
        )

        msg_content = (
            f'您的广告投放申请「{apply[3]}」未通过审核。\n'
            f'驳回原因：{body.reason}\n'
            f'审核时间：{now.strftime("%Y-%m-%d %H:%M")}\n'
            f'如有疑问，请修改后重新提交申请。'
        )
        await mongodb.insert_one('commodity_msg', {
            'mall_id': apply[1],
            'shopping_id': apply[2],
            'msg': msg_content,
            'pass': 0,
            'auditor': username,
            'read': 0,
        })

        cache = CacheService(redis)
        await cache.delete_pattern("ad:apply:*")
        await cache.delete_pattern("commodity:inform:*")

        return {"current": True, "msg": "已驳回"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
