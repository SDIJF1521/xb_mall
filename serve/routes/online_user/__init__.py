from typing import Annotated

from fastapi import APIRouter,Form,Depends,HTTPException

from services.on_line import OnLine
from data.data_mods import UserOnLineUploading


def get_redis():
    from main import redis_client
    return redis_client

router = APIRouter()

@router.post('/online_user')
async def online_user(data:Annotated[UserOnLineUploading,Form()],redis_clien=Depends(get_redis)) -> dict:
    """
    用户上线
    """
    try:
        online = OnLine(redis_client=redis_clien, token=data.token)
        await online.wait_init()
        return await online.up_line()
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')
