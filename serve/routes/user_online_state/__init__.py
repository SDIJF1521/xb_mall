from typing import Annotated

from fastapi import APIRouter,Form,Depends,HTTPException

from data.data_mods import UserOnLineUploading
from services.on_line import OnLine

router = APIRouter()

def get_redis():
    from main import redis_client
    return redis_client

@router.post('/user_online_state')
async def user_online_state(data:Annotated[UserOnLineUploading,Form()],redis_client=Depends(get_redis)):
    """
    查询用户在线状态
    """
    try:
        online = OnLine(redis_client=redis_client,token=data.token)
        await online.wait_init()
        return await online.on_line_state()
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')