from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from services.cache_service import CacheService
from data.file_client import read_file_base64_with_cache

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()


@router.get('/ad_banner_active')
async def ad_banner_active(
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """公共接口：获取当前生效的轮播图广告列表（按排序展示）"""
    try:
        cache = CacheService(redis)
        cache_key = "ad:banner:active"
        cached = await cache.get(cache_key)
        if cached is not None:
            return {"current": True, "data": cached}

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        rows = await execute_db_query(
            db,
            """SELECT b.id, b.mall_id, b.shopping_id, b.title, b.img_path,
                      s.mall_name
               FROM ad_banner b
               LEFT JOIN store s ON b.mall_id = s.mall_id
               WHERE b.is_active = 1 AND b.start_time <= %s AND b.end_time >= %s
               ORDER BY b.sort_order ASC, b.created_at DESC
               LIMIT 10""",
            (now, now)
        )

        items = []
        if rows:
            for r in rows:
                mall_id, shopping_id = r[1], r[2]
                banner_img_path = r[4]

                mongo_doc = await mongodb.find_one('shopping', {'mall_id': mall_id, 'shopping_id': shopping_id})
                commodity_name = mongo_doc.get('name', '') if mongo_doc else ''
                img_list = mongo_doc.get('img_list', []) if mongo_doc else []

                img_path = banner_img_path or (img_list[0] if img_list else None)
                img_b64 = ""
                if img_path:
                    img_b64 = await read_file_base64_with_cache(img_path, redis, cache_expire=1800)

                if img_b64:
                    items.append({
                        "id": r[0], "mall_id": mall_id, "shopping_id": shopping_id,
                        "title": r[3], "img": img_b64,
                        "mall_name": r[5], "commodity_name": commodity_name,
                    })

        await cache.set(cache_key, items, expire=120)

        return {"current": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
