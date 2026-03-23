from data.redis_client import RedisClient
from services.manage_token_issue import issue_admin_tokens


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
        tokens = await issue_admin_tokens(self.user, self.redis_client)
        return {
            'msg': '登录成功',
            'current': True,
            **tokens,
        }