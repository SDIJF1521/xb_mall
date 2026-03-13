import jwt
from data.redis_client import RedisClient
from config.jwt_config import jwt_settings
class LogIn:
    def __init__(self,token):
        self.token = token
    async def run(self,data,redis_cli:RedisClient) -> bool:
        SECRET_KEY = jwt_settings.JWT_USER_SECRET_KEY
        try:
            token = self.token.split(" ")[1]
            payload:dict = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user = payload.get("user")
            expire_timestamp = payload.get("exp")
            #print(user)
            # print(data)
            data_list = [i[0] for i in data]
            if user is None:
                return {'msg':'无法验证',"current":False}
            if user in data_list:
                if await redis_cli.get(f"user_{user}") == expire_timestamp:
                    return {'msg':'验证通过',"current":True}
                else:
                    return {'msg':'token已过期',"current":False}
            else:
                return {'msg':'用户非法',"current":False}
        except jwt.InvalidTokenError:
            return {'msg':'无效的 token',"current":False}
        except jwt.ExpiredSignatureError:
            return {'mag':'token已过期',"current":False}