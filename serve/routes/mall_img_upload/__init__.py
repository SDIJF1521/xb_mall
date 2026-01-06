from typing import Annotated
import imghdr
import os

from fastapi import APIRouter,Depends,HTTPException,Form,File,UploadFile
import aiomysql

from services.verify_duter_token import VerifyDuterToken
from services.cache_service import CacheService

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient
from data.data_mods import AddMallImg

def get_redis():
    from main import redis_client
    return redis_client

router = APIRouter()

@router.post('/mall_img_upload')
async def mall_img_upload(
    token: str = Form(...),
    id: str = Form(...),
    mall_img: UploadFile = File(...),
    db: aiomysql.Connection = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    """
    上传店铺图片
    """
    verify = VerifyDuterToken(token,redis)
    token_data = await verify.token_data()
    sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
    verify_val = await verify.verify_token(sql_data=sql_data)
    if verify_val[0]:
        if verify_val[1] in ['seller', 'admin']:
            contents = await mall_img.read()
            image_format = imghdr.what(None, contents)
            if not image_format:
                image_format = 'jpeg'
            
            img_path = f'./mall_img/{id}.png'
            
            if os.path.exists(img_path):
                os.remove(img_path)
            
            with open(img_path,'wb') as f:
                f.write(contents)
                await execute_db_query(db,'UPDATE store SET img_path=%s WHERE mall_id=%s', (img_path, id))
            
            cache = CacheService(redis)
            await cache.delete_pattern(f"mall_info:*")
            
            return {'code':200,'msg':'上传成功','current':True}
        else:
            raise HTTPException(status_code=403, detail="权限不足")
    else:
        raise HTTPException(status_code=401, detail="token验证失败")