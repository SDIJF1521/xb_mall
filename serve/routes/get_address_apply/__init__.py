import aiomysql
from fastapi import APIRouter,Form,Depends,HTTPException

from services.user_info import UserInfo
from data.sql_client import get_db,execute_db_query

router = APIRouter()
@router.post('/get_address_apply')
async def get_address_apply(token:str = Form(min_length=6),db:aiomysql.Connection = Depends(get_db)):
    user_info = UserInfo(token)
    user_info_data = await user_info.token_analysis()
    if user_info_data['current']:
        user_data = await execute_db_query(db,'select name,phone,save,city,county,address,apply_option from user_address where user = %s and apply_option = %s',
                                           (user_info_data['user'],1))
        if user_data:
            return {'msg':'查询成功','current':True,'data':user_data[0]}
        else:
            return {'msg':'查询失败','current':False}
    else:
        return {'msg':'token无效','current':False}