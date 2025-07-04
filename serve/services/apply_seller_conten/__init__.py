from ..user_info import UserInfo

class ApplySellerConten:
    def __init__(self,token:str):
        self.token = token
    async def content(self,sql_data):
        sql_name = []
        if sql_data:
            sql_name = [i[0] for i in sql_data]
        else:
            return {'msg': '没有商家申请数据', 'current': False}
        data = await UserInfo(self.token).token_analysis()
        if data['current']:

            if data['user'] in sql_name:
                index = sql_name.index(data['user'])
                return {
                    'name': sql_data[index][1],
                    'phone': sql_data[index][2],
                    'mall_name': sql_data[index][3],
                    'mall_describe': sql_data[index][4],
                    'current': True
                }
            else:
                return {'msg': '您还没有申请商家', 'current': False}
            
        else:
            return {'msg': 'token无效或已过期', 'current': False}