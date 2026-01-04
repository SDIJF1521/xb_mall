

import aiomysql
from fastapi import APIRouter,Depends,HTTPException,Query
from data.sql_client import get_db,execute_db_query


router = APIRouter()

@router.get('/get_address_options')
async def get_address_options(save:str = None,
                              city:str=None,
                              db:aiomysql.Connection=Depends(get_db)):
    """
    获取省市区地址选项接口（三级联动）
    流程：查询省份列表 -> 根据省份查询城市 -> 根据城市查询区县
    用途：地址选择器的数据源，支持三级联动
    """
    try:
        # 查询所有省份（parent_id=0表示顶级）
        save_list = [i[0] for i in await execute_db_query(db,'select name from dou_area where parent_id = %s',0)]
        city_list = []
        county_list = []
        
        # 如果提供了省份，查询该省份下的城市
        if not save is None:
            save_id = await execute_db_query(db,'select area_id from dou_area where name = %s',save)
            city_list = [i[0] for i in await execute_db_query(db,'select name from dou_area where parent_id = %s',save_id[0][0])]
        
        # 如果提供了城市，查询该城市下的区县
        if not city is None:
            city_id = await execute_db_query(db,'select area_id from dou_area where name = %s',city)
            county_list = [i[0] for i in await execute_db_query(db,'select name from dou_area where parent_id = %s',city_id[0][0])]
        
        return {
            'save_list':save_list,
            'city_list':city_list,
            'county_list':county_list
    }
    except:
        raise HTTPException(status_code=400,detail='获取地址选项失败')