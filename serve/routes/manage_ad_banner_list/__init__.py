from fastapi import APIRouter, Depends, Header, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from data.file_client import read_file_base64_with_cache

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.data_mods import ManageAdBannerListQuery

router = APIRouter()


@router.get('/manage_ad_banner_list')
async def manage_ad_banner_list(
    query: ManageAdBannerListQuery = Depends(),
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """平台端：获取轮播图广告管理列表"""
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.system_settings"
        )
        if not ok:
            return {"current": False, "msg": msg}

        where_clauses = []
        params = []
        if query.is_active is not None:
            where_clauses.append("b.is_active = %s")
            params.append(query.is_active)

        where_sql = (" AND " + " AND ".join(where_clauses)) if where_clauses else ""

        count_sql = f"SELECT COUNT(*) FROM ad_banner b WHERE 1=1 {where_sql}"
        count_row = await execute_db_query(db, count_sql, tuple(params))
        total = int(count_row[0][0]) if count_row else 0

        offset = (query.page - 1) * query.page_size
        params_page = list(params) + [query.page_size, offset]

        data_sql = f"""
            SELECT b.id, b.apply_id, b.mall_id, b.shopping_id, b.title,
                   b.img_path, b.sort_order, b.is_active,
                   b.start_time, b.end_time, b.created_at,
                   s.mall_name
            FROM ad_banner b
            LEFT JOIN store s ON b.mall_id = s.mall_id
            WHERE 1=1 {where_sql}
            ORDER BY b.sort_order ASC, b.created_at DESC
            LIMIT %s OFFSET %s
        """
        rows = await execute_db_query(db, data_sql, tuple(params_page))

        items = []
        if rows:
            for r in rows:
                mall_id, shopping_id = r[2], r[3]
                banner_img_path = r[5]

                mongo_doc = await mongodb.find_one('shopping', {'mall_id': mall_id, 'shopping_id': shopping_id})
                commodity_name = mongo_doc.get('name', '') if mongo_doc else ''
                img_list = mongo_doc.get('img_list', []) if mongo_doc else []

                img_path = banner_img_path or (img_list[0] if img_list else None)
                img_b64 = ""
                if img_path:
                    img_b64 = await read_file_base64_with_cache(img_path, redis, cache_expire=1800)

                items.append({
                    "id": r[0], "apply_id": r[1], "mall_id": mall_id,
                    "shopping_id": shopping_id, "title": r[4], "img": img_b64,
                    "sort_order": r[6], "is_active": r[7],
                    "start_time": str(r[8]) if r[8] else None,
                    "end_time": str(r[9]) if r[9] else None,
                    "created_at": str(r[10]) if r[10] else None,
                    "mall_name": r[11], "commodity_name": commodity_name,
                })

        return {
            "current": True,
            "data": items,
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
