from pydantic import EmailStr
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

def get_verifier():
    # 从 main.py 引入 verifier 实例
    from main import verifier
    return verifier

@router.get("/verification_code")
async def get_verification_code(email: EmailStr, verifier = Depends(get_verifier)):
    """
    获取邮箱验证码接口
    流程：检查冷却时间 -> 生成验证码 -> 存储到Redis -> 发送邮件
    特性：60秒冷却时间，5分钟有效期，验证后自动删除
    """
    try:
        # 使用邮箱作为用户ID
        user_id = f"email:{email}"
        # 发送验证码邮件（包含冷却时间检查）
        success, remaining = await verifier.send_verification_email(user_id, email)

        if success:
            return {"code": 200, "message": "验证码已发送", "current": True}
        else:
            # 冷却时间未到，返回剩余等待时间
            return {"code": 429, "message": f"请等待 {remaining} 秒后再试", "current": False}
    except Exception as e:
        print(f"发送验证码失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")