from ..user_info import UserInfo

class UserInfoAmend:
    def __init__(self,nickname,age,sex):
        self.nickname = nickname
        self.age = age
        self.sex = sex
    async def wrute(self,token):
        """
        个人信息修改的SQL语句
        """
        current_token = await UserInfo(token).token_analysis()
        if current_token['current']:
            return {'query':'UPDATE personal_details SET nickname = %s, age= %s, sex= %s WHERE user = %s','params':(self.nickname,self.age,self.sex,current_token['user']),'current':True}
        else:
            return current_token