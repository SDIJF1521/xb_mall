from typing import Annotated
from datetime import date

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form

from services.verify_duter_token import VerifyDuterToken

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.data_mods import AddMallData

router = APIRouter()

@router.post("/add_mall")
async def add_mall(data:Annotated[AddMallData,Form()],db:Connection=Depends(get_db),redis:RedisClient=Depends(get_redis)):
    """
    管理员添加店铺接口
    流程：管理员Token验证 -> 检查店长账号是否存在 -> 创建店铺记录 -> 返回店铺ID
    权限：仅管理员可操作
    """
    verify_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_token.token_data()
    sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
    verity_val = await verify_token.verify_token(sql_data=sql_data)
    if verity_val[0]:
        if verity_val[1] != 'admin':
            return {'msg':'权限不足','current':False}
        elif verity_val[1] == 'admin':
            # 检查店长账号是否存在（必须已有seller_sing记录）
            sql_user_admin = await execute_db_query(db,"select user from seller_sing where user = %s",(data.user))
            if not sql_user_admin:
                return {'msg':'选择的用户没有店长账号不能设置为店长,','current':False,'code':200}
            
            # 创建店铺记录（state=1表示正常状态）
            await execute_db_query(db,
                                   'INSERT INTO store (mall_name,user,mall_phone,mall_site,mall_describe,creation_time,state) values (%s,%s,%s,%s,%s,%s,%s)',
                                   (data.mall_name,data.user,data.mall_phone,data.mall_site,data.info,date.today(),1))
            # 获取新增店铺的ID
            sql_prod_id = await execute_db_query(db,'SELECT LAST_INSERT_ID() AS prod_id;')
            prod_id = sql_prod_id[0][0]
            return {'msg':'添加成功','prod_id':prod_id,'current':True,'code':200}
        else:
            return {'msg':'权限不足','current':False,'code':403}
    else:
        return {'msg':'token验证失败','current':False,'code':401}