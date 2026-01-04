from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,UploadFile,File

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis

router = APIRouter()

@router.patch('/buyer_update_img')
async def buyer_update_img(token:str = Form(...),id:str = Form(...),img:UploadFile=File(...),db:Connection=Depends(get_db),redis:RedisClient=Depends(get_redis)):
    """
    更新店铺图片接口
    流程：Token验证 -> 权限检查 -> 保存图片文件
    权限：主商户直接通过，店铺用户需要写入权限[1]、查询权限[2]和分配权限[4]
    """
    verify_duter_token = VerifyDuterToken(token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute():
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            # 保存店铺图片到本地（文件命名：店铺ID.png）
            with open(f"./mall_img/{id}.png", "wb") as f:
                f.write(await img.read())
            return {"code":200,"msg":"success","data":None,'current':True}
        else:
            return {"code":400,"msg":"token验证失败","data":None,'current':False}

    if token_data.get('station') == '1':
        return await execute()
    else:
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        # 需要写入权限[1]、查询权限[2]和分配权限[4]
        if execute_code[1] and execute_code[2] and execute_code[4] and verify_data:
            return await execute()
        else:
            return {"code":400,"msg":"权限不足","data":None,'current':False}