import os

from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile

from services.verify_duter_token import VerifyDuterToken
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()


@router.post('/buyer_ad_apply')
async def buyer_ad_apply(
    token: str = Form(...),
    stroe_id: int = Form(...),
    shopping_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    duration_days: int = Form(7),
    ad_img: UploadFile = File(None),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """商家端：提交广告投放申请"""
    try:
        verify = VerifyDuterToken(token, redis)
        token_data = await verify.token_data()
        sql_data = await execute_db_query(
            db, 'SELECT user FROM seller_sing WHERE user = %s', (token_data.get('user'),)
        )
        verify_val = await verify.verify_token(sql_data=sql_data)
        if not verify_val[0]:
            return {"current": False, "msg": "身份验证失败"}
        if verify_val[1] not in ['seller', 'admin']:
            return {"current": False, "msg": "权限不足"}

        shopping_row = await execute_db_query(
            db,
            "SELECT shopping_id FROM shopping WHERE shopping_id = %s AND mall_id = %s",
            (shopping_id, stroe_id)
        )
        if not shopping_row:
            return {"current": False, "msg": "商品不存在或不属于该店铺"}

        pending = await execute_db_query(
            db,
            "SELECT id FROM ad_apply WHERE mall_id = %s AND shopping_id = %s AND status = 'pending'",
            (stroe_id, shopping_id)
        )
        if pending:
            return {"current": False, "msg": "该商品已有待审核的投放申请"}

        img_path = None
        if ad_img and ad_img.filename:
            os.makedirs('./ad_img', exist_ok=True)
            contents = await ad_img.read()
            img_path = f'./ad_img/ad_{stroe_id}_{shopping_id}.png'
            with open(img_path, 'wb') as f:
                f.write(contents)

        await execute_db_query(
            db,
            """INSERT INTO ad_apply (mall_id, shopping_id, title, description, img_path, duration_days)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (stroe_id, shopping_id, title, description, img_path, duration_days)
        )

        cache = CacheService(redis)
        await cache.delete_pattern("ad:apply:*")

        return {"current": True, "msg": "投放申请已提交，请等待平台审核"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
