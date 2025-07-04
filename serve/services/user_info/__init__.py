import jwt
class UserInfo:
    def __init__(self,token):
        self.token = token
    async def token_analysis(self):
        SECRET_KEY = "$@?123App"
        try:
            token = self.token.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user = payload.get("user")
            return {'user':user,"current":True}
        except jwt.InvalidTokenError:
            return {'msg':'无效的 token',"current":False}
        except jwt.ExpiredSignatureError:
            return {'msg':'token已过期',"current":False}
    async def read(self,user:tuple):
        if not user:
            raise ValueError('当前没有用户')
        user_list = [i[0] for i in user]
        user_name = await self.token_analysis()
        if user_name['current']:
            if user_name['user'] in user_list:
                return {'query': 'select * From personal_details WHERE user =  %s', 
                    'params': (user_name['user']),
                    "current":True}
            else:
                return {'msg':'当前用户无权限',"current":False}
        else:
            return user_name

