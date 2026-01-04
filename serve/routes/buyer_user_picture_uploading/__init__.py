
from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,UploadFile,File

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient

router = APIRouter()

@router.post("/buyer_user_picture_uploading")
async def buyer_user_picture_uploading(token:str = Form(...),
                                       stroe_id:int = Form(...),
                                       name:str = Form(...),
                                       file:UploadFile = File(...),
                                       db:Connection = Depends(get_db),
                                       redis_client:RedisClient = Depends(get_redis)
                                       ):
    """
    上传店铺用户头像接口
    流程：Token验证 -> 权限检查 -> 保存图片文件 -> 更新数据库记录
    权限：主商户直接通过，店铺用户需要查询权限[2]、删除权限[3]和分配权限[4]
    """
    verify_duter_token = VerifyDuterToken(token,redis_client)
    token_data = await verify_duter_token.token_data()

    async def execute(user:str) ->dict:
        # 保存图片到本地（文件命名：店铺ID_用户名.png）
        with open(f"./buyer_use_img/{stroe_id}_{name}.png", "wb") as f:
            f.write(await file.read())
        # 更新用户头像路径
        await execute_db_query(db,'update store_user set img = %s where user = %s and store_id = %s',(f"./buyer_use_img/{stroe_id}_{name}.png",name,stroe_id))
        return {"code":200,"msg":"success","data":None,'current':True}
    
    if token_data.get('station') == '1':
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            return await execute(name)
    else:
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        # 需要查询权限[2]、删除权限[3]和分配权限[4]
        if execute_code[2] and execute_code[3] and execute_code[4] and verify_data:
            return await execute(name)
        else:
            return {"code":400,"msg":"权限不足","data":None,'current':False}