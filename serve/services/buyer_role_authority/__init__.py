from aiomysql import Connection
from data.sql_client import execute_db_query

# 角色权限服务
class RoleAuthorityService:
    def __init__(self, role,db:Connection):
        self.db = db
        self.role = role
    async def get_authority(self,mall_id: int):
        sql = 'select id from store_role where id = %s and (mall_id = %s or mall_id is Null)'
        execute_code = await execute_db_query(self.db,sql,(self.role,mall_id))

        if execute_code:
            sql_1 = 'select authority from  role_authority where role_id = %s and (mall_id = %s or mall_id is Null)'
            execute_code = await execute_db_query(self.db,sql_1,(execute_code[0][0],mall_id))
        return execute_code
    async def authority_resolver(self,role_execute_code:int):
        
        execute_code = await execute_db_query(self.db,'select * from role_code')
        
        if execute_code:
            role_out = []
            execute_code_dict = {i[0]:i[1] for i in execute_code}
            for i in execute_code_dict:
                if role_execute_code & i:
                    role_out.append(True)
                else:
                    role_out.append(False)
            return role_out
        else:
            return None