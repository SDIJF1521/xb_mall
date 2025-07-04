from datetime import datetime, timedelta

import jwt

class ManageLogin:
    def __init__(self,user:str,password:str):
        self.user = user
        self.password = password
    
    async def check_password(self,sql_data:tuple):
        admin_list = [i[0] for i in sql_data]
        if self.user not in admin_list:
            return {'msg':'用户不存在','current':False}
        if self.password != sql_data[admin_list.index(self.user)][1]:
            return {'msg':'密码错误','current':False}
        # 生成token
        expire_minutes = 7
        expire = datetime.utcnow() + timedelta(days=expire_minutes)
        SECRET_KEY = '1352%!#$@awdS'
        payload = {
                    'user': self.user,
                    'exp':expire
                }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return {'msg':'登录成功','current':True,'token':token, "token_type": "bearer"}