import aiomysql
from fastapi import APIRouter, Depends, Form,File, HTTPException

from data.sql_client import get_db, execute_db_query
from services.uploading_photo import UploadingPhoto

router = APIRouter()

@router.patch('/uploading_profile_photo')
async def uploading_profile_photo(file: bytes = File(),token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db)) -> dict:
    """
    上传用户头像接口
    流程：Token验证 -> 保存图片文件 -> 更新数据库头像路径
    用途：用户修改个人头像
    """
    try:
        uploading = UploadingPhoto(file)
        # 验证Token并保存头像文件
        data = await uploading.uploading(token)
        if data['current']:
            # 更新数据库中的头像路径
            await execute_db_query(db,data['query'],data['params'])
            return {'msg':'头像上传成功','current':True}
        else:
            return {'msg':'头像上传失败,无法验证用户','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')