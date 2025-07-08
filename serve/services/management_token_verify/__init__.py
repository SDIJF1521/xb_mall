import jwt

from data.redis_client import RedisClient
class ManagementTokenVerify:
    def __init__(self,token,redis_client: RedisClient):
        self.token = token
        self.redis_client = redis_client

    async def token_admin(self):
        try:
            SECRET_KEY = "1352%!#$@awdS"
            token = self.token.split(" ")[1]
            payload:dict = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user = payload.get("user")
            return {"current":True,'user':user}
        except jwt.InvalidTokenError:
            return {'msg':'无效的 token',"current":False}
        except jwt.ExpiredSignatureError:
            return {'mag':'token已过期',"current":False}

    async def run(self,data) -> bool:
        SECRET_KEY = "1352%!#$@awdS"
        try:
            token = self.token.split(" ")[1]
            payload:dict = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user = payload.get("user")
            data_list = [i[0] for i in data]
            if user is None:
                return {'msg':'无法验证',"current":False}
            if user in data_list:
                if payload.get('exp') != str(await self.redis_client.get(f'admin_{user}')):
                    return {'msg':'token已过期',"current":False}
                return {'msg':'验证通过',"current":True}
            else:
                return {'msg':'用户非法',"current":False}
        except jwt.InvalidTokenError:
            return {'msg':'无效的 token',"current":False}
        except jwt.ExpiredSignatureError:
            return {'mag':'token已过期',"current":False}