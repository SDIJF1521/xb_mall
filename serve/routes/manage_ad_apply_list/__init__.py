from fastapi import APIRouter, Depends, Header, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from data.file_client import read_file_base64_with_cache

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.data_mods import ManageAdApplyListQuery

router = APIRouter()


@router.get('/manage_ad_apply_list')
async def manage_ad_apply_list(
    query: ManageAdApplyListQuery = Depends(),
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """平台端：获取广告投放申请列表"""
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.system_settings"
        )
        if not ok:
            return {"current": False, "msg": msg}

        where_clauses = []
        params = []

        if query.status:
            where_clauses.append("a.status = %s")
            params.append(query.status)

        where_sql = (" AND " + " AND ".join(where_clauses)) if where_clauses else ""

        # 如果有搜索关键词，先从 MongoDB 查店铺名/标题匹配
        if query.select_data:
            where_clauses_extra = "(a.title LIKE %s OR s.mall_name LIKE %s)"
            where_sql += f" AND {where_clauses_extra}" if where_sql else f" AND {where_clauses_extra}"
            kw = f"%{query.select_data}%"
            params.extend([kw, kw])

        count_sql = f"""
            SELECT COUNT(*) FROM ad_apply a
            LEFT JOIN store s ON a.mall_id = s.mall_id
            WHERE 1=1 {where_sql}
        """
        count_row = await execute_db_query(db, count_sql, tuple(params))
        total = int(count_row[0][0]) if count_row else 0

        offset = (query.page - 1) * query.page_size
        params_page = list(params) + [query.page_size, offset]

        data_sql = f"""
            SELECT a.id, a.mall_id, a.shopping_id, a.title, a.description,
                   a.img_path, a.duration_days, a.status, a.reject_reason,
                   a.apply_time, a.review_time, a.reviewer,
                   s.mall_name
            FROM ad_apply a
            LEFT JOIN store s ON a.mall_id = s.mall_id
            WHERE 1=1 {where_sql}
            ORDER BY
                CASE a.status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END,
                a.apply_time DESC
            LIMIT %s OFFSET %s
        """
        rows = await execute_db_query(db, data_sql, tuple(params_page))

        items = []
        if rows:
            for r in rows:
                mall_id, shopping_id = r[1], r[2]
                ad_img_path = r[5]

                mongo_doc = await mongodb.find_one('shopping', {'mall_id': mall_id, 'shopping_id': shopping_id})
                commodity_name = mongo_doc.get('name', '') if mongo_doc else ''
                img_list = mongo_doc.get('img_list', []) if mongo_doc else []

                img_path = ad_img_path or (img_list[0] if img_list else None)
                img_b64 = ""
                if img_path:
                    img_b64 = await read_file_base64_with_cache(img_path, redis, cache_expire=1800)

                items.append({
                    "id": r[0], "mall_id": mall_id, "shopping_id": shopping_id,
                    "title": r[3], "description": r[4], "img": img_b64,
                    "duration_days": r[6], "status": r[7], "reject_reason": r[8],
                    "apply_time": str(r[9]) if r[9] else None,
                    "review_time": str(r[10]) if r[10] else None,
                    "reviewer": r[11], "mall_name": r[12],
                    "commodity_name": commodity_name,
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
