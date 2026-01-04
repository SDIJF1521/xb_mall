from typing import Annotated

import aiomysql
from fastapi import APIRouter,Form,Depends, HTTPException

from services.user_info import UserInfo
from data.data_mods import UserAddressModify
from data.sql_client import get_db,execute_db_query

router = APIRouter()

@router.patch('/modify_address')
async def modify_address(data:Annotated[UserAddressModify,Form()],db:aiomysql.Connection=Depends(get_db)):
    """
    修改用户收货地址接口
    流程：Token验证 -> 验证地址归属（防止越权）-> 更新地址信息
    安全：验证地址是否属于当前用户，防止修改他人地址
    """
    try:
        token_user_info = UserInfo(token=data.token)
        token_user_data = await token_user_info.token_analysis()
        if token_user_data['current']:
            # 验证地址是否属于当前用户（防止越权修改）
            sql_address = await execute_db_query(db,'select user from user_address where address_id = %s',data.id)
            if sql_address:
                if sql_address[0][0] == token_user_data['user']:
                    # 更新地址信息（省市区、详细地址、姓名、电话）
                    await execute_db_query(db,'update user_address set save = %s,city = %s,county = %s,address = %s,name = %s,phone = %s where address_id = %s',
                                            (data.save,data.city,data.county,data.address,data.name,data.phone,data.id))
                    return {'msg':'修改成功','current':True}
                else:
                    return {'msg':'该用户还没有相关地址数据','current':False}
            else:
                return {'msg':'没有相关地址信息','current':False}
        else:
            raise HTTPException(status_code=401, detail="未授权")
    except Exception as e:
          raise HTTPException(status_code=500,detail=str(e))
