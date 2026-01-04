from typing import Annotated

import jwt

from fastapi import APIRouter,Form,Depends

from data.redis_client import RedisClient,get_redis
from data.data_mods import DeleteToken


router = APIRouter()

@router.delete('/delete_token_time')
async def delete_token_time(data:Annotated[DeleteToken,Form()],redis_cli:RedisClient=Depends(get_redis)):
    """
    删除Token过期时间接口（强制登出）
    流程：根据用户类型解析Token -> 删除Redis中的Token过期时间记录
    用途：主动登出，使Token失效
    类型：genre=1普通用户，genre=2商户，genre=3管理员
    """
    identity_dic = {
        "1":'user',
        "2":'seller',
        "3":'admin'
    }
    secret_key_dic={
        "user":'$@?123App',
        "seller":"$@?%^159ASx",
        "admin":"1352%!#$@awdS"
    }
    token = data.token.split(" ")[1]

    # 普通用户Token删除
    if data.genre == '1':
        try:
            payload:dict = jwt.decode(token,secret_key_dic[identity_dic[data.genre]],algorithms=['HS256'])
            user = payload.get("user")
            # 删除Redis中的Token过期时间（使Token失效）
            await redis_cli.delete(f"user_{user}")
            return {'msg':'删除成功','current':True}
        except jwt.InvalidTokenError:
            return {'msg':'无效的 token','current':False}
        except jwt.ExpiredSignatureError:
            return {'msg':'token已过期','current':False}
        except Exception as e:
            return {'msg':str(e),'current':False}
    # 商户Token删除
    elif data.genre == "2":
        try:
            payload:dict = jwt.decode(token,secret_key_dic[identity_dic[data.genre]],algorithms=['HS256'])
            seller = payload.get("seller")
            await redis_cli.delete(f"buyer_{seller}")
            return {'msg':'删除成功','current':True}
        except jwt.InvalidTokenError:
            return {'msg':'无效的 token','current':False}
        except jwt.ExpiredSignatureError:
            return {'msg':'token已过期','current':False}
        except Exception as e:
            return {'msg':str(e),'current':False}
    # 管理员Token删除
    elif data.genre == "3":
        try:
            payload:dict = jwt.decode(token,secret_key_dic[identity_dic[data.genre]],algorithms=['HS256'])
            admin = payload.get("admin")
            await redis_cli.delete(f"admin_{admin}")
            return {'msg':'删除成功','current':True}
        except jwt.InvalidTokenError:
            return {'msg':'无效的 token','current':False}
        except jwt.ExpiredSignatureError:
            return {'msg':'token已过期','current':False}
        except Exception as e:
            return {'msg':str(e),'current':False}
    else:
        return {'msg':' genre 错误','current':False}
