from datetime import date

import jwt


class Register:
    def __init__(self, user: str, email: str, password: str, code: str):
        self.email = email
        self.password = password
        self.code = code
        self.user = user
    
    async def verify(self):
        SECRET_KEY = "$@#233"
        if not self.code:
            return '缺少 Authorization 头部'
        try:
            token = self.code.split(" ")[1]
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
    
    async def user_add(self, existing_users: list,email_list:list):
        existing_users = [i[0] for i in existing_users]
        email_list = [i[0] for i in email_list]
        # 验证用户名
        if len(self.user) == 0:
            return '用户名不能为空'
        
        # 验证密码长度
        if len(self.password) < 8:  # 修正为小于8
            return '密码长度要大于或等于8'
        
        # 检查密码复杂度
        has_digit = any(c.isdigit() for c in self.password)
        has_letter = any(c.isalpha() for c in self.password)
        
        if not (has_digit and has_letter):  # 修正逻辑：必须同时包含数字和字母
            return '密码必须包含数字和字母'
        
        # 验证token
        verify_result = await self.verify()  # 异步调用
        if verify_result is not True:
            return [verify_result]
        
        # 检查用户名是否已存在
        if self.user in existing_users:
            return '用户名已存在请重新选择用户名'
        # 检查邮箱是否已存在
        if self.email in email_list:
            return '该邮箱已被注册'
        
        # 返回SQL插入语句和参数
        print(date.today())
        return {1:{'query': 'INSERT INTO user(user, password,email,merchant,time) VALUES(%s, %s,%s,%s,%s)', 
                'params': (self.user, self.password,self.email,0,date.today())},
                2:{'query':'INSERT INTO personal_details(user,nickname) VALUES(%s,%s)',
                   'params':(self.user,self.user)},
                3:{'query':'INSERT INTO user_address(user) VALUES(%s)','params':(self.user)}
                   }
