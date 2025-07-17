from typing import Annotated

import aiomysql
from fastapi import APIRouter,Form,Depends,HTTPException

from services.user_info import UserInfo
from data.data_mods import UserAddress
from data.sql_client import get_db,execute_db_query

router = APIRouter()


@router.post('/add_address')
async def add_address(data:Annotated[UserAddress,Form()],db:aiomysql.Connection=Depends(get_db)):
    token_user_info = UserInfo(token=data.token)
    try:
        token_user_data = await token_user_info.token_analysis()
        if token_user_data['current']:
            # 获取数据库对应用户地址数据
            sql_address = await execute_db_query(db,'select address_id from user_address where user = %s',token_user_data['user'])
            # 查询是否已有对应内容
            sql_repeat_data = await execute_db_query(db,'select * from user_address where user = %s and name = %s and phone=%s and save = %s and city=%s and county=%s and address=%s',(token_user_data['user'],data.name,data.phone,data.save,data.city,data.county,data.address))
            if sql_repeat_data:
                return {'msg':'重复数据','current':False}
            print(sql_repeat_data)
            await execute_db_query(db,'insert into user_address (user,name,phone,save,city,county,address) values (%s,%s,%s,%s,%s,%s,%s)',
                                    (token_user_data['user'],data.name,data.phone,data.save,data.city,data.county,data.address))
            return {'msg':'添加成功','current':True}
        else:
            raise HTTPException(status_code=401, detail="未授权")
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))  