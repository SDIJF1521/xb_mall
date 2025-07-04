import aiomysql
from fastapi import APIRouter,Depends,HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from data.sql_client import get_db, execute_db_query

from services.log_in_token import Token

router = APIRouter()
@router.post('/token')
async def user_token(form_data: OAuth2PasswordRequestForm = Depends(), db:aiomysql.Connection = Depends(get_db)) -> dict:
    try:
        database_data = await execute_db_query(db,'select user,password FROM user WhERE user = %s',form_data.username)
        token = Token(form_data.username,form_data.password)
        return await token.make(database_data)
    except Exception as e:
          raise HTTPException(status_code=500, detail="服务器内部错误")