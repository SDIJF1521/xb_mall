import jwt
class PasswordReplacement:
    def __init__(self,email,password,token):
        self.email = email
        self.password = password
        self.token = token
    
    async def verify(self):
        SECRET_KEY = "$@#233"
        if not self.token:
            return '缺少 Authorization 头部'
        try:
            token = self.token.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            email = payload.get("user")
            if email is None:
                return '无法验证'
            if f"email:{self.email}" == email:
                return True
            else:
                return '用户非法'
        except jwt.InvalidTokenError:
            return '无效的 token'
        except jwt.ExpiredSignatureError:
            return 'token已过期'
    
    async def replacement(self,email_list):
        select = self.verify()
        if not select is True:
            if self.email in email_list:
                return {'query':'UPDATE user SET password=%s WHERE email = %s','params':(self.password,self.email),'current':True}
            else:
                return '用户不存在'
        else:
            return '验证异常'