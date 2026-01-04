import aiomysql
from fastapi import APIRouter,HTTPException,Depends,Form

from services.management_token_verify import ManagementTokenVerify

from data.sql_client import execute_db_query,get_db

def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()

@router.post('/management_verify')
async def management_verify(token:str=Form(min_length=6),db:aiomysql.Connection = Depends(get_db),redis_client=Depends(get_redis)):
    """
    管理员Token验证接口
    流程：解析Token -> 验证管理员权限 -> 检查Redis过期时间
    用途：前端路由守卫调用，验证管理员登录状态
    """
    try:
        management_token_verify = ManagementTokenVerify(token=token,redis_client=redis_client)
        admin_tokrn_content = await management_token_verify.token_admin()
        if admin_tokrn_content['current']:
            admin = admin_tokrn_content['user']
            # 查询管理员信息并验证Token有效性
            data = await execute_db_query(db,f'select * from manage_user where user = "{admin}"')
            return await management_token_verify.run(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
