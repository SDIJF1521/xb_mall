from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.data_mods import ManageAdApplyApprove

router = APIRouter()


@router.post('/manage_ad_apply_approve')
async def manage_ad_apply_approve(
    body: ManageAdApplyApprove,
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """平台端：审批通过广告投放申请，自动生成轮播图记录"""
    try:
        ok, msg, username = await verify_admin_with_permission(
            db, redis, access_token, required="admin.system_settings"
        )
        if not ok:
            return {"current": False, "msg": msg}

        row = await execute_db_query(
            db,
            "SELECT id, mall_id, shopping_id, title, img_path, duration_days, status "
            "FROM ad_apply WHERE id = %s",
            (body.apply_id,)
        )
        if not row:
            return {"current": False, "msg": "申请不存在"}
        apply = row[0]
        if apply[6] != 'pending':
            return {"current": False, "msg": "该申请已处理"}

        now = datetime.now()
        end_time = now + timedelta(days=apply[5])

        await execute_db_query(
            db,
            "UPDATE ad_apply SET status='approved', review_time=%s, reviewer=%s WHERE id=%s",
            (now, username, body.apply_id)
        )

        img_path = apply[4]
        if not img_path:
            mongo_doc = await mongodb.find_one('shopping', {'mall_id': apply[1], 'shopping_id': apply[2]})
            if mongo_doc:
                img_list = mongo_doc.get('img_list', [])
                if img_list:
                    img_path = img_list[0]

        await execute_db_query(
            db,
            """INSERT INTO ad_banner (apply_id, mall_id, shopping_id, title, img_path,
                   sort_order, is_active, start_time, end_time)
               VALUES (%s, %s, %s, %s, %s, 0, 1, %s, %s)""",
            (body.apply_id, apply[1], apply[2], apply[3], img_path, now, end_time)
        )

        remark = body.remark or '无'
        msg_content = (
            f'您的广告投放申请「{apply[3]}」已审核通过！\n'
            f'投放时长：{apply[5]} 天\n'
            f'上线时间：{now.strftime("%Y-%m-%d %H:%M")}\n'
            f'备注：{remark}'
        )
        await mongodb.insert_one('commodity_msg', {
            'mall_id': apply[1],
            'shopping_id': apply[2],
            'msg': msg_content,
            'pass': 1,
            'auditor': username,
            'read': 0,
        })

        cache = CacheService(redis)
        await cache.delete_pattern("ad:banner:*")
        await cache.delete_pattern("ad:apply:*")
        await cache.delete_pattern("commodity:inform:*")

        return {"current": True, "msg": "已通过，轮播广告已上线"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
