from pydantic import EmailStr
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

def get_verifier():
    # 从 main.py 引入 verifier 实例
    from main import verifier
    return verifier

@router.get("/verification_code")
async def get_verification_code(email: EmailStr, verifier = Depends(get_verifier)):
    """获取邮箱验证码"""
    try:
        # 使用邮箱作为用户ID
        user_id = f"email:{email}"
        # 发送验证码邮件
        success, remaining = await verifier.send_verification_email(user_id, email)

        if success:
            return {"code": 200, "message": "验证码已发送", "current": True}
        else:
            return {"code": 429, "message": f"请等待 {remaining} 秒后再试", "current": False}
    except Exception as e:
        print(f"发送验证码失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")