import aiomysql

from fastapi import APIRouter,Depends,Form,HTTPException

from data.sql_client import get_db,execute_db_query
from services.user_info import UserInfo

router = APIRouter()

@router.post('/user_data')
async def user_data(token:str = Form(min_length=6),db:aiomysql.Connection = Depends(get_db)):
    user_info = UserInfo(token)
    user_info_data = await user_info.token_analysis()
    if user_info_data['current']:
        user_data = await execute_db_query(db,'select * from user where user = %s',user_info_data['user'])
        if user_data:
            return {'msg':'查询成功','current':True,'data':[user_data[0][0],user_data[0][3]]}
        else:
            return {'msg':'查询失败','current':False}
    else:
        return {'msg':'token无效','current':False}