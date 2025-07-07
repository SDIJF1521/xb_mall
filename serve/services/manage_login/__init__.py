from datetime import datetime, timedelta

import jwt

from data.redis_client import RedisClient

class ManageLogin:
    def __init__(self,user:str,password:str,redis_client: RedisClient):
        self.user = user
        self.password = password
        self.redis_client = redis_client
    
    async def check_password(self,sql_data:tuple):
        admin_list = [i[0] for i in sql_data]
        if self.user not in admin_list:
            return {'msg':'用户不存在','current':False}
        if self.password != sql_data[admin_list.index(self.user)][1]:
            return {'msg':'密码错误','current':False}
        # 生成token
        expire_minutes = 7
        
        expire = datetime.utcnow() + timedelta(days=expire_minutes)
        expire_timestamp = int(expire.timestamp())
        await self.redis_client.set(f'admin_{self.user}',expire_timestamp)

        SECRET_KEY = '1352%!#$@awdS'
        payload = {
                    'user': self.user,
                    'exp':str(expire_timestamp)
                }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return {'msg':'登录成功','current':True,'token':token, "token_type": "bearer"}