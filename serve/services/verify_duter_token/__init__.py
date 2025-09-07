import jwt
from data.redis_client import RedisClient

class VerifyDuterToken:
    def __init__(self,token:str,redis_client:RedisClient):
        self.redis_client = redis_client


        self.token = token
        self.SECRET_KEY = "$@?%^159ASx"
    async def token_data(self):
        try:
            token = self.token.split(" ")[1]
            payload:dict = jwt.decode(token, self.SECRET_KEY, algorithms=['HS256'])
            return payload

        except:
            return None
    
    async def verify_token(self,sql_data):

        token_data = await self.token_data()

        if not token_data is None:
            if token_data.get('station') == '1':

                if sql_data and token_data.get('exp') == str(await self.redis_client.get(f'buyer_{token_data.get("user")}')):
                    return [True,"admin"]
                else:
                    return [False]
            elif token_data['station'] == '2':
                if sql_data and token_data.get('exp') == str(self.redis_client.get(f'buyer_{token_data.get("user")}')):
                    return [True,"user"]
                else:
                    return [False]
            else:
                return [False]
        else:
            return [False]
