from typing import Annotated

from fastapi import APIRouter,Depends,HTTPException,Form
import aiomysql

from services.verify_duter_token import VerifyDuterToken

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient
from data.data_mods import AddMallImg

def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()

#  定义卖家上传店铺图片路由
@router.post('/mall_img_upload')
async def mall_img_upload(data:Annotated[AddMallImg,Form()], db:aiomysql.Connection = Depends(get_db),redis:RedisClient=Depends(get_redis)):
    # 验证 token
    verify = VerifyDuterToken(data.token,redis)
    token_data = await verify.token_data()
    sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
    verify_val = await verify.verify_token(sql_data=sql_data)
    if verify_val[0]:
        # 检查用户权限
        print(verify_val[1])
        if verify_val[1] == 'seller':
            raise HTTPException(status_code=403, detail="权限不足")
        elif verify_val[1] == 'admin':
            # 管理员权限，允许上传
            with open(f'./mall_img/{data.id}.jpg','wb') as f:
                f.write(data.mall_img)
                # 上传到数据库
                print(f'./mall_img/{data.id}.jpg')
                await execute_db_query(db,'UPDATE store SET img_path=%s WHERE mall_id=%s', (f'./mall_img/{data.id}.jpg', data.id))
            return {'code':200,'msg':'上传成功','current':True}
        else:
            raise HTTPException(status_code=403, detail="权限不足")
    else:
        raise HTTPException(status_code=401, detail="token验证失败")