import jwt

from data.redis_client import RedisClient
from config.jwt_config import jwt_settings


def _raw_jwt(token: str) -> str:
    t = (token or "").strip()
    if t.lower().startswith("bearer "):
        return t.split(" ", 1)[1].strip()
    return t


class ManagementTokenVerify:
    def __init__(self,token,redis_client: RedisClient):
        self.token = token
        self.redis_client = redis_client

    async def token_admin(self):
        try:
            SECRET_KEY = jwt_settings.JWT_ADMIN_SECRET_KEY
            raw = _raw_jwt(self.token)
            payload:dict = jwt.decode(
                raw, SECRET_KEY, algorithms=['HS256'],
                options={"verify_signature": True, "verify_exp": False},
            )
            if payload.get("typ") == "refresh":
                return {'msg':'请使用 access_token',"current":False}
            user = payload.get("user")
            return {"current":True,'user':user}
        except jwt.ExpiredSignatureError:
            return {'msg':'token已过期',"current":False}
        except jwt.InvalidTokenError:
            return {'msg':'无效的 token',"current":False}

    async def run(self,data) -> bool:
        SECRET_KEY = jwt_settings.JWT_ADMIN_SECRET_KEY
        try:
            raw = _raw_jwt(self.token)
            payload:dict = jwt.decode(
                raw, SECRET_KEY, algorithms=['HS256'],
                options={"verify_signature": True, "verify_exp": False},
            )
            if payload.get("typ") == "refresh":
                return {'msg':'请使用 access_token',"current":False}
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
        except jwt.ExpiredSignatureError:
            return {'msg':'token已过期',"current":False}
        except jwt.InvalidTokenError:
            return {'msg':'无效的 token',"current":False}