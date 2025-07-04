import aiomysql
from fastapi import APIRouter, Depends, Form,File, HTTPException

from data.sql_client import get_db, execute_db_query
from services.uploading_photo import UploadingPhoto

router = APIRouter()
@router.patch('/uploading_profile_photo')
async def uploading_profile_photo(file: bytes = File(),token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db)) -> dict:
    try:
        uploading = UploadingPhoto(file)
        data = await uploading.uploading(token)
        if data['current']:
            await execute_db_query(db,data['query'],data['params'])
            return {'msg':'头像上传成功','current':True}
        else:
            return {'msg':'头像上传失败,无法验证用户','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')