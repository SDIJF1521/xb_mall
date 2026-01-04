from typing import Annotated

from fastapi import APIRouter,Depends,Form,HTTPException

from data.data_mods import UserOnLineUploading
from services.on_line import OnLine

def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()

@router.patch('/online_heartbeat')
async def online_heartbeat(data:Annotated[UserOnLineUploading,Form()],redis_client=Depends(get_redis)):
    """
    用户在线心跳接口
    流程：解析Token -> 更新Redis中的在线状态时间戳
    用途：前端定时调用，保持用户在线状态，定时任务会清理离线用户
    """
    try:
        online = OnLine(redis_client=redis_client,token=data.token)
        await online.wait_init()
        # 更新在线状态时间戳（心跳）
        return await online.on_line_heartbeat()
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')