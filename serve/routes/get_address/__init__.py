import aiomysql

from fastapi import APIRouter,Depends,Form,HTTPException
from services.user_info import UserInfo
from services.cache_service import CacheService
from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient

router = APIRouter()

@router.post('/get_address')
async def get_address_options(token=Form(min_length=6),db:aiomysql.Connection=Depends(get_db),redis:RedisClient=Depends(get_redis)):
    """
    获取用户收货地址列表
    返回：地址列表（包含地址ID、姓名、电话、省市区、详细地址、申请状态）
    """
    try:
        token_user_info = UserInfo(token=token)
        token_user_data = await token_user_info.token_analysis()
        if token_user_data['current']:
            cache = CacheService(redis)
            cache_key = cache._make_key('user:address', token_user_data['user'])
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
            
            sql_save = await execute_db_query(db,
                                            'SELECT ROW_NUMBER() OVER (ORDER BY user DESC) AS temp_id,address_id,name,phone,save,city,county,address,apply_option FROM user_address WHERE user = %s',
                                            token_user_data['user'])
            if sql_save:
                out_dic:dict = {}
                if len(sql_save) == 1:
                    out_dic.update({0:list(sql_save[0])})
                    result = {'current':True,'save_list':out_dic}
                else:
                    for  i in range(len(sql_save)):
                        out_dic.update({i:list(sql_save[i])})
                    result = {'current':True,'save_list':out_dic}
                await cache.set(cache_key, result, expire=300)
                return result
            return {'current':False,'msg':'目前还没有地址'}

        else:
            raise HTTPException(status_code=401, detail="未授权")
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

