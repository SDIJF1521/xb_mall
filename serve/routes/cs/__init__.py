from aiomysql import Connection

from fastapi import APIRouter,Query,Depends

from services.buyer_role_authority import RoleAuthorityService
from data.sql_client import get_db,execute_db_query


router = APIRouter()
@router.get('/cs')
async def get_cs(data:int=Query(...,description='角色id'), db: Connection = Depends(get_db)):
    role_authority_service = RoleAuthorityService(data,db)
    role_authority = await role_authority_service.get_authority(6)
    print(role_authority[0][0])
    return await role_authority_service.authority_resolver(int(role_authority[0][0]))
