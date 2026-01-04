import aiomysql
from fastapi import APIRouter,Form,Depends,HTTPException

from services.user_info import UserInfo
from data.sql_client import get_db,execute_db_query

router = APIRouter()

@router.post('/get_address_apply')
async def get_address_apply(token:str = Form(min_length=6),db:aiomysql.Connection = Depends(get_db)):
    """
    获取用户默认收货地址接口
    流程：Token验证 -> 查询默认地址（apply_option=1）
    用途：获取用户当前设置的默认收货地址
    """
    user_info = UserInfo(token)
    user_info_data = await user_info.token_analysis()
    if user_info_data['current']:
        # 查询用户的默认地址（apply_option=1表示默认地址）
        user_data = await execute_db_query(db,'select name,phone,save,city,county,address,apply_option from user_address where user = %s and apply_option = %s',
                                           (user_info_data['user'],1))
        if user_data:
            return {'msg':'查询成功','current':True,'data':user_data[0]}
        else:
            return {'msg':'查询失败','current':False}
    else:
        return {'msg':'token无效','current':False}