import aiomysql

from fastapi import APIRouter,Depends,Form,HTTPException
from services.user_info import UserInfo
from data.sql_client import get_db,execute_db_query

router = APIRouter()
@router.post('/get_address')
async def get_address_options(token=Form(min_length=6),db:aiomysql.Connection=Depends(get_db)):
    try:
        token_user_info = UserInfo(token=token)
        token_user_data = await token_user_info.token_analysis()
        if token_user_data['current']:
            sql_save = await execute_db_query(db,
                                            'SELECT ROW_NUMBER() OVER (ORDER BY user DESC) AS temp_id,address_id,name,phone,save,city,county,address FROM user_address WHERE user = %s',
                                            token_user_data['user'])
            if sql_save:
                out_dic:dict = {}
                if len(sql_save) == 1:
                    out_dic.update({0:list(sql_save[0])})
                    return {'current':True,'save_list':out_dic}
                else:
                    for  i in range(len(sql_save)):
                        out_dic.update({i:list(sql_save[i])})
                    return {'current':True,'save_list':out_dic}
            return {'current':False,'msg':'目前还没有地址'}

        else:
            raise HTTPException(status_code=401, detail="未授权")
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

