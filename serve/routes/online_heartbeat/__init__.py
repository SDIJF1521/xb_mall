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
    try:
        online = OnLine(redis_client=redis_client,token=data.token)
        await online.wait_init()
        return await online.on_line_heartbeat()
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')