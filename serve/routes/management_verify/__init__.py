import aiomysql
from fastapi import APIRouter,HTTPException,Depends,Form

from services.management_token_verify import ManagementTokenVerify

from data.sql_client import execute_db_query,get_db

router = APIRouter()
@router.post('/management_verify')
async def management_verify(token:str=Form(min_length=6),db:aiomysql.Connection = Depends(get_db)):
    try:
        management_token_verify = ManagementTokenVerify(token)
        data = await execute_db_query(db,'select user from manage_user')
        return await management_token_verify.run(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
