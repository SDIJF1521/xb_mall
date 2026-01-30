from aiomysql import Connection
from data.sql_client import execute_db_query
from services.cache_service import CacheService
from data.redis_client import RedisClient

# 角色权限服务 - 基于位运算的权限管理系统
class RoleAuthorityService:
    def __init__(self, role,db:Connection,redis:RedisClient,name:str,mall_id:int):
        self.db = db
        self.role = role
        self.name = name
        self.mall_id = mall_id
        self.redis = redis
        self.cache_service: CacheService = CacheService(self.redis)
    
    async def get_authority(self,mall_id: int):
        """获取角色权限码（支持店铺级和全局权限）"""
        cached_data = await self.cache_service.get(f'role:list:{self.mall_id}:{self.name}')
        print('no')
        if cached_data is not None:
            return cached_data
        sql = 'select id from store_role where id = %s and (mall_id = %s or mall_id is Null)'
        execute_code = await execute_db_query(self.db,sql,(self.role,mall_id))

        if execute_code:
            sql_1 = 'select authority from  role_authority where role_id = %s and (mall_id = %s or mall_id is Null)'
            execute_code = await execute_db_query(self.db,sql_1,(execute_code[0][0],mall_id))
        await self.cache_service.set(f'role:list:{self.mall_id}:{self.name}',execute_code)
        return execute_code
    
    async def authority_resolver(self,role_execute_code:int):
        """
        权限码解析器 - 使用位运算将权限码转换为权限列表
        返回列表索引对应关系：
        [0] = 添加权限, [1] = 写入权限, [2] = 查询权限, [3] = 删除权限, [4] = 分配权限
        例如：权限码 5 (二进制: 101) 表示拥有添加权限和删除权限
        """
        role_out = await self.cache_service.get(f'role:{self.mall_id}:{self.name}')
        print('yes')
        if role_out is not None:
            return role_out
        execute_code = await execute_db_query(self.db,'select * from role_code')
        
        if execute_code:
            role_out = []
            execute_code_dict = {i[0]:i[1] for i in execute_code}
            # 位运算检查：role_execute_code & i 判断是否拥有该权限
            for i in execute_code_dict:
                if role_execute_code & i:
                    role_out.append(True)
                else:
                    role_out.append(False)
            await self.cache_service.set(f'role:{self.mall_id}:{self.name}',role_out)
            return role_out
        else:
            return None