from datetime import datetime, timedelta
import time

import jwt
from pydantic import EmailStr
from fastapi import APIRouter, Depends, HTTPException


router = APIRouter()

def get_verifier():
    
    # 从 main.py 引入 verifier 实例
    from main import verifier
    return verifier
@router.post('/verify_code')
async def verify_code(email: EmailStr, code: str,verifier = Depends(get_verifier)) -> dict:
    """验证验证码"""
    try:
        # 使用邮箱作为用户ID
        user_id=f"email:{email}"
        
        # 验证验证码
        is_valid=await verifier.verify_code(user_id, code)
        
        if is_valid:
            expire_minutes = 5
            expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
            payload = {
                'user': user_id,
                'code': code,
                'exp':expire
            }
            SECRET_KEY = "$@#233"
            return {"code": 200, "message": "验证成功", "data": {"access_token": jwt.encode(payload, SECRET_KEY, algorithm="HS256"), "token_type": "bearer",
            'timestamp': time.time()}}
        else:
            return {"code": 400, "message": "验证码错误或已过期", "data": None}
    except Exception as e:
        print(f"验证验证码失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"验证验证码失败: {str(e)},服务器内部错误")
