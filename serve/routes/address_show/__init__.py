

import aiomysql
from fastapi import APIRouter,Depends,HTTPException,Query
from data.sql_client import get_db,execute_db_query


router = APIRouter()

# 定义地址选项获取路由
@router.get('/get_address_options')
async def get_address_options(save:str = None,
                              city:str=None,
                              db:aiomysql.Connection=Depends(get_db)):
    save_list = [i[0] for i in await execute_db_query(db,'select name from dou_area where parent_id = %s',0)]
    city_list = []
    county_list = []
    if not save is None:
        save_id = await execute_db_query(db,'select area_id from dou_area where name = %s',save)
        city_list = [i[0] for i in await execute_db_query(db,'select name from dou_area where parent_id = %s',save_id[0][0])]
    if not city is None:
        city_id = await execute_db_query(db,'select area_id from dou_area where name = %s',city)
        county_list = [i[0] for i in await execute_db_query(db,'select name from dou_area where parent_id = %s',city_id[0][0])]
    return {
        'save_list':save_list,
        'city_list':city_list,
        'county_list':county_list
    }
    # except:
    #     raise HTTPException(status_code=400,detail='获取地址选项失败')