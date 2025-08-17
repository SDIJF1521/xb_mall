from typing import Annotated

from fastapi import FastAPI, Form, Query
from fastapi.middleware.cors import CORSMiddleware

from data.data_mods import AddMall, DeleteMall, UserOnLineUploading
from services.verification_code import VerificationCode
from data.redis_client import RedisClient
from contextlib import asynccontextmanager
    
from routes.verification_code import router as verification_router
from routes.verify_code import router as verify_code_router
from routes.register import router as register_router
from routes.token import router as token_router
from routes.user_sign_in import router as user_sign_in_router
from routes.password_reset import router as password_reset_router
from routes.userinfo import router as userinfo_router
from routes.user_data import router as user_data_router
from routes.apply_seller import router as apply_seller_router
from routes.user_data_amend import router as user_data_amend_router
from routes.uploading_profile_photo import router as uploading_profile_photo_router
from routes.get_apply_seller_content import router as get_apply_seller_content_router
from routes.add_address import router as add_address_router
from routes.get_address import router as get_address_router
from routes.address_apply import router as address_apply_router
from routes.get_address_apply import router as get_address_apply_router
from routes.modify_address import router as modify_address_router
from routes.delete_address import router as delete_address_router
from routes.online_user import router as online_user_router
from routes.get_online_user_list import router as get_online_user_list_router
from routes.online_heartbeat import router as online_heartbeat_router
from routes.online_off import router as online_off_router
from routes.user_online_state import router as user_online_state_router
from routes.manage_sign_in import router as manage_sign_in_router
from routes.management_verify import router as management_verify_router
from routes.management_mall_info import router as management_mall_info_router
from routes.user_list import router as user_list_router
from routes.today_user_list import router as today_user_list_router
from routes.number_merchants import router as number_merchants_router
from routes.get_apply_seller_list import router as get_apply_seller_list_router
from routes.get_name_apply_seller_user import router as get_name_apply_seller_user_router
from routes.apply_seller_consent import router as apply_seller_consent_router
from routes.apply_seller_reject import router as apply_seller_reject_router
from routes.address_show import router as address_show_router


redis_client = RedisClient()
# 定义 lifespan 事件处理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理，处理启动和关闭事件。
    在应用启动时连接 Redis，关闭时断开连接。
    """
    try:
        # 应用启动时的逻辑
        await redis_client.connect()
        await verifier.connect()  # 连接验证码模块的 Redis 客户端
        print("Redis 连接已建立")
        yield
    except Exception as e:
        print(f"应用启动失败: {str(e)}")
    finally:
        # 应用关闭时的逻辑
        await redis_client.close()
        await verifier.close()  # 关闭验证码模块的 Redis 客户端
        print("Redis 连接已关闭")

# 注册fatsApi应用
app = FastAPI(lifespan=lifespan)

# 定义跨域资源中间件
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 邮箱配置
email_config = {
    "sender_email": "3574747175@qq.com",
    "sender_password": "dusbvohhfaiucifi",
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "use_ssl": True
}

# 创建全局验证码实例
verifier = VerificationCode(redis_url="redis://localhost",email_config=email_config)

# 验证码申请路由
app.include_router(verification_router, prefix="/api")

# 验证码验证路由
app.include_router(verify_code_router,prefix='/api')

# 注册路由
app.include_router(register_router,prefix='/api')

# 生成token路由
app.include_router(token_router,prefix='/api')

# 登录路由
app.include_router(user_sign_in_router,prefix='/api')

# 重置密码路由
app.include_router(password_reset_router,prefix='/api')

# 用户信息查询路由
app.include_router(userinfo_router,prefix='/api')

# 商家申请路由
app.include_router(apply_seller_router,prefix='/api')

# 头像上传路由
app.include_router(uploading_profile_photo_router,prefix='/api')

# 基础信息修改路由
app.include_router(user_data_amend_router,prefix='/api')

# 用户数据路由
app.include_router(user_data_router,prefix='/api')

# 获取商家申请内容路由
app.include_router(get_apply_seller_content_router,prefix='/api')

# 上传在线用户路由
app.include_router(online_user_router, prefix='/api')

# 获取在线用户列表
app.include_router(get_online_user_list_router,prefix='/api')

# 地址添加路由
app.include_router(add_address_router,prefix='/api')

# 地址获取路由
app.include_router(get_address_router,prefix='/api')

# 地址修改路由
app.include_router(modify_address_router,prefix='/api')

# 地址删除路由
app.include_router(delete_address_router,prefix='/api')

# 地址应用路由
app.include_router(address_apply_router,prefix='/api')

# 获取应用地址路由
app.include_router(get_address_apply_router,prefix='/api')

# 在线用户心跳请求路由
app.include_router(online_heartbeat_router,prefix='/api')

# 用户状态
app.include_router(user_online_state_router,prefix='/api')

# 在线用户下线请求路由
app.include_router(online_off_router,prefix='/api')

# 地址选项获取路由
app.include_router(address_show_router,prefix='/api')

# 管理员登录路由
app.include_router(manage_sign_in_router,prefix='/api')

# 管理员验证路由
app.include_router(management_verify_router,prefix='/api')

# 获取用户列表路由
app.include_router(user_list_router,prefix='/api')

# 获取商家列表路由
app.include_router(number_merchants_router,prefix='/api')

# 当日新增用户列表
app.include_router(today_user_list_router,prefix='/api')

# 获取商家申请列表路由
app.include_router(get_apply_seller_list_router,prefix='/api')

# 获取用户申请商家路由
app.include_router(get_name_apply_seller_user_router,prefix='/api')

# 同意商家申请路由
app.include_router(apply_seller_consent_router,prefix='/api')

# 拒绝商家申请路由
app.include_router(apply_seller_reject_router,prefix='/api')

# 获取商家信息路由
app.include_router(management_mall_info_router,prefix='/api')

# 商品添加路由
@app.patch('/Product_upload')
async def product_upload(data: Annotated[AddMall, Form()])->list:
    pass

# 商品查询路由
@app.get('/select')
async def select(name:str = Query(alias='type',min_length=1)):
    pass

# 商品删除路由
@app.delete('/mall_delete')
async def mall_delete(data:Annotated[DeleteMall,Form()])->dict:
    pass