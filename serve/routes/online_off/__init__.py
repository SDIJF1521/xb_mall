from typing import Annotated

from fastapi import APIRouter, HTTPException,  Form,Depends

from data.data_mods import UserOnLineUploading
from services.on_line import OnLine

def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()

@router.delete('/online_off')
async def online_off(data:Annotated[UserOnLineUploading,Form()],redis_client=Depends(get_redis)):
    """
    用户下线接口
    流程：解析Token -> 删除Redis在线状态 -> 更新数据库状态
    用途：用户登出时调用，清除在线状态
    """
    try:
        online = OnLine(redis_client=redis_client,token=data.token)
        await online.wait_init()
        # 清除用户在线状态
        return await online.off_line()
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')