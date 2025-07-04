from typing import Annotated

import aiomysql
from fastapi import APIRouter, Depends,Form,HTTPException

from data.data_mods import UserInformation
from data.sql_client import get_db, execute_db_query
from services.user_info_amend import UserInfoAmend

router = APIRouter()
@router.patch('/user_data_amend')
async def user_data_amend(data:Annotated[UserInformation,Form()], db:aiomysql.Connection = Depends(get_db)) -> dict:
    try:
        uploading = UserInfoAmend(nickname = data.nickname,age=data.age,sex=data.sex)
        data = await uploading.wrute(data.token)
        if data['current']:
            await execute_db_query(db,data['query'],data['params'])
            return {'msg':'信息更改成功','current':True}
        else:
            return {'msg':'信息更改失败，无法验证用户','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')