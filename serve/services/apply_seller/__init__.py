import datetime
from ..user_info import UserInfo
class ApplySeller:
    def __init__(self,name:str,phone:str,mall_name:str,mall_describe:str):
        self.name = name
        self.phone = phone
        self.mall_name = mall_name
        self.mall_describe = mall_describe
    
    async def apply(self,sql_data, token:str):

        sql_name = []
        if sql_data:
            sql_name = [i[0] for i in sql_data]
        data = await UserInfo(token).token_analysis()
        if data['current']:
            if data['user'] not in sql_name:
                return {
                    'query': 'INSERT INTO shop_apply (user, name, phone, mall_name, describe_mall,time) VALUES (%s, %s, %s, %s, %s,%s)',
                    'params': (data['user'],self.name, self.phone, self.mall_name, self.mall_describe,datetime.date.today()),
                    'current': True
                }
            elif sql_data[sql_name.index(data['user'])][5] != 3:
                return {
                    'query': 'UPDATE shop_apply SET name = %s, phone = %s, mall_name = %s, describe_mall = %s , time = %sWHERE user = %s',
                    'params': (self.name, self.phone, self.mall_name, self.mall_describe, datetime.date.today(),data['user']),
                    'current': True
                }
            else:
                return {'msg': '您已经申请过商家了', 'current': False}
        else:
            return {'msg': 'token无效或已过期', 'current': False}