import os

from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis

router = APIRouter()


@router.post('/buyer_ad_apply_img')
async def buyer_ad_apply_img(
    token: str = Form(...),
    apply_id: int = Form(...),
    ad_img: UploadFile = File(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端：为已有申请上传/更新广告图片"""
    try:
        verify = VerifyDuterToken(token, redis)
        token_data = await verify.token_data()
        if not token_data:
            return {"current": False, "msg": "Token 无效"}

        station = token_data.get('station')

        if station == '1':
            sql_data = await execute_db_query(
                db, 'SELECT user FROM seller_sing WHERE user = %s', (token_data.get('user'),)
            )
            verify_val = await verify.verify_token(sql_data=sql_data)
            if not verify_val[0]:
                return {"current": False, "msg": "身份验证失败"}
        elif station == '2':
            user = token_data.get('user')
            mall_id = token_data.get('mall_id')
            role_svc = RoleAuthorityService(
                role=token_data.get('role'), db=db, redis=redis,
                name=user, mall_id=mall_id,
            )
            role_authority = await role_svc.get_authority(mall_id)
            if not role_authority:
                return {"current": False, "msg": "未找到角色权限"}
            execute_code = await role_svc.authority_resolver(int(role_authority[0][0]))
            sql_data = await execute_db_query(
                db, 'SELECT user FROM store_user WHERE user = %s AND store_id = %s',
                (user, mall_id),
            )
            verify_val = await verify.verify_token(sql_data=sql_data)
            if not (execute_code[1] and verify_val[0]):
                return {"current": False, "msg": "您没有权限执行此操作"}
        else:
            return {"current": False, "msg": "未知的身份类型"}

        row = await execute_db_query(
            db, "SELECT mall_id, shopping_id FROM ad_apply WHERE id = %s", (apply_id,)
        )
        if not row:
            return {"current": False, "msg": "申请不存在"}

        mall_id, shopping_id = row[0]

        os.makedirs('./ad_img', exist_ok=True)
        contents = await ad_img.read()
        img_path = f'./ad_img/ad_{mall_id}_{shopping_id}.png'
        with open(img_path, 'wb') as f:
            f.write(contents)

        await execute_db_query(
            db, "UPDATE ad_apply SET img_path = %s WHERE id = %s", (img_path, apply_id)
        )

        return {"current": True, "msg": "图片上传成功", "img_path": img_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
