from fastapi import APIRouter, Depends, Header, HTTPException

from services.verify_duter_token import VerifyDuterToken

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.data_mods import BuyerAdApplyListQuery

router = APIRouter()


@router.get('/buyer_ad_apply_list')
async def buyer_ad_apply_list(
    query: BuyerAdApplyListQuery = Depends(),
    token: str = Header(..., alias="access-token"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """商家端：获取本店铺的广告投放申请列表"""
    try:
        verify = VerifyDuterToken(token, redis)
        token_data = await verify.token_data()
        sql_data = await execute_db_query(
            db, 'SELECT user FROM seller_sing WHERE user = %s', (token_data.get('user'),)
        )
        verify_val = await verify.verify_token(sql_data=sql_data)
        if not verify_val[0]:
            return {"current": False, "msg": "身份验证失败"}

        where_clauses = ["a.mall_id = %s"]
        params = [query.stroe_id]

        if query.status:
            where_clauses.append("a.status = %s")
            params.append(query.status)

        where_sql = " AND ".join(where_clauses)

        count_row = await execute_db_query(
            db, f"SELECT COUNT(*) FROM ad_apply a WHERE {where_sql}", tuple(params)
        )
        total = int(count_row[0][0]) if count_row else 0

        offset = (query.page - 1) * query.page_size
        params_page = list(params) + [query.page_size, offset]

        rows = await execute_db_query(
            db,
            f"""SELECT a.id, a.shopping_id, a.title, a.description, a.img_path,
                       a.duration_days, a.status, a.reject_reason,
                       a.apply_time, a.review_time, a.mall_id
                FROM ad_apply a
                WHERE {where_sql}
                ORDER BY a.apply_time DESC
                LIMIT %s OFFSET %s""",
            tuple(params_page)
        )

        items = []
        if rows:
            for r in rows:
                shopping_id = r[1]
                mall_id = r[10]
                mongo_doc = await mongodb.find_one('shopping', {'mall_id': mall_id, 'shopping_id': shopping_id})
                commodity_name = mongo_doc.get('name', '') if mongo_doc else ''

                items.append({
                    "id": r[0], "shopping_id": shopping_id, "title": r[2],
                    "description": r[3], "img_path": r[4],
                    "duration_days": r[5], "status": r[6], "reject_reason": r[7],
                    "apply_time": str(r[8]) if r[8] else None,
                    "review_time": str(r[9]) if r[9] else None,
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
