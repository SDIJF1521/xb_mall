import aiomysql
from fastapi import APIRouter, Depends, Form,File, HTTPException

from data.sql_client import get_db, execute_db_query
from data.redis_client import get_redis,RedisClient
from services.uploading_photo import UploadingPhoto
from services.user_info import UserInfo
from services.cache_service import CacheService

router = APIRouter()

@router.patch('/uploading_profile_photo')
async def uploading_profile_photo(file: bytes = File(),token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db),redis:RedisClient=Depends(get_redis)) -> dict:
    """
    上传用户头像
    """
    try:
        uploading = UploadingPhoto(file)
        data = await uploading.uploading(token)
        if data['current']:
            await execute_db_query(db,data['query'],data['params'])
            
            user_info = UserInfo(token)
            user_data = await user_info.token_analysis()
            if user_data.get('current'):
                cache = CacheService(redis)
                cache_key = cache._make_key('user:info', user_data['user'])
                await cache.delete(cache_key)
                
                img_path = f'./img/{user_data["user"]}.jpg'
                img_cache_key = cache._make_key('img_base64', img_path)
                await cache.delete(img_cache_key)
            
            return {'msg':'头像上传成功','current':True}
        else:
            return {'msg':'头像上传失败,无法验证用户','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')