import jwt
import base64
from datetime import datetime, timedelta
from data.redis_client import RedisClient
class Token:
    def __init__(self,username:str,password:str):
        self.username = username
        self.password = password
    async def make(self,data,redis_cli:RedisClient):
        if not data:
            return {'msg':'没有该用户名','token':None}
        else:
            if data[0][1] == self.password:
                SECRET_KEY = "$@?123App"
                expire_minutes = 7
                expire = datetime.utcnow() + timedelta(days=expire_minutes)
                expire_timestamp = int(expire.timestamp())
                payload = {
                    'user': self.username,
                    'exp': str(expire_timestamp)
                }
                await redis_cli.set(f"user_{self.username}",str(expire_timestamp))
                return {'msg':'token生成成功','token':jwt.encode(payload, SECRET_KEY, algorithm="HS256"),"token_type": "bearer"}
            else:
                return {'msg':'密码错误','token':None}       