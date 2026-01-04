import jwt
from data.redis_client import RedisClient

class VerifyDuterToken:
    """商户端Token验证服务 - 区分主商户(station=1)和店铺用户(station=2)"""
    
    def __init__(self,token:str,redis_client:RedisClient):
        self.redis_client = redis_client
        self.token = token
        self.SECRET_KEY = "$@?%^159ASx"
    
    async def token_data(self):
        """解析JWT Token获取载荷数据"""
        try:
            token = self.token.split(" ")[1]
            payload:dict = jwt.decode(token, self.SECRET_KEY, algorithms=['HS256'])
            return payload
        except:
            return None
    
    async def verify_token(self,sql_data):
        """
        Token验证逻辑：
        - station='1': 主商户（可管理多个店铺）
        - station='2': 店铺用户（只能管理指定店铺）
        - 通过Redis验证Token过期时间，防止Token被篡改
        """
        token_data = await self.token_data()

        if not token_data is None:
            # 主商户验证：检查Redis中的过期时间是否匹配
            if token_data.get('station') == '1' and token_data.get('state') == 1:
                if sql_data and token_data.get('exp') == str(await self.redis_client.get(f'buyer_{token_data.get("user")}')):
                    return [True,"admin"]
                else:
                    return [False]
            # 店铺用户验证：需要同时验证店铺ID和用户
            elif token_data['station'] == '2' and token_data.get('state') == 1:
                if sql_data and token_data.get('exp') == str(await self.redis_client.get(f'buyer_{token_data.get("mall_id")}_{token_data.get("user")}')):
                    return [True,"user"]
                else:
                    return [False]
            else:
                return [False]
        else:
            return [False]
