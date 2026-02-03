import os
import sys
import time
import asyncio
from typing import Annotated

import logging
import fastapi_cdn_host
from fastapi import FastAPI, Form, Query,Request,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.log_config import logger
from config.redis_config import settings as redis_settings
from config.mongodb_config import settings as mongodb_settings
from config.sql_config import settings as sql_settings

from data.data_mods import AddMall, DeleteMall, UserOnLineUploading
from services.verification_code import VerificationCode
from data.redis_client import RedisClient
from data.mongodb_client import mongodb_client
from data.sql_client import get_db,execute_db_query
from data.sql_client_pool import db_pool
from starlette.middleware.base import BaseHTTPMiddleware
    
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
from routes.buyer_side_token import router as buyer_side_token_router
from routes.buyer_side_sgin import router as buyer_side_sgin_router
from routes.mall_img_upload import router as mall_img_upload_router
from routes.add_mall import router as add_mall_router
from routes.buyer_repeat_show import router as buyer_repeat_show_router
from routes.buyer_get_mall_name import router as buyer_get_mall_name_router
from routes.buyer_delete_show import router as buyer_delete_show_router
from routes.buyer_get_mall_info import router as buyer_get_mall_info_router
from routes.buyer_update_mall import router as buyer_update_mall_router
from routes.buyer_img_update import router as buyer_img_update_router
from routes.buyer_mall_user_list import router as buyer_mall_user_list_router
from routes.buyer_user_add import router as buyer_user_add_router
from routes.buyer_user_picture_uploading import router as buyer_user_picture_uploading_router
from routes.buyer_user_select import router as buyer_user_select_router
from routes.buyer_user_delete import router as buyer_user_delete_router
from routes.buyer_amend_user import router as buyer_amend_user_router
from routes.buyer_get_role import router as buyer_get_role_router
from routes.buyter_role_code_get import router as buter_role_code_get_router
from routes.buyer_role_add import router as buyer_role_add_router
from routes.buyter_delete_role import router as buyter_delete_role_router
from routes.buyer_role_info import router as buyer_role_info_router
from routes.buyer_update_role import router as buyer_update_role_router
from routes.buyer_role_ratio import router as buyer_role_ratio_router
from routes.buyer_commoidt_add import router as buyer_commoidt_add_router
from routes.buyer_get_classify import router as get_classify_router
from routes.buyer_get_commoidt import router as buyer_get_commoidt_router
from routes.buyer_commodity_inform import router as buyer_commodity_inform_router
from routes.buyer_commodity_inform_read import router as buyer_r_commodity_inform_read_router
from routes.buyer_commodity_inform_delete import router as buyer_commodity_inform_delete_router
from routes.buyer_commodity_edit import router as buyer_commodity_edit_router
from routes.buyer_commodity_delete import router as buyer_commodity_delete_router
from routes.buyer_commodity_delisting import router as buyer_commodity_delisting_router
from routes.buyer_commoidt_putaway import router as buyer_commodity_putaway_router
from routes.buyer_classify_add import router as buyer_classify_add_router
from routes.buyer_classify_delete import router as buyer_classify_delete_router
from routes.buyer_classify_edit import router as  buyer_classify_edit_router
from routes.buyer_commodity_repertory_list import router as buyer_commodity_repertory_list_router
from routes.buyer_commodity_repertory_statistics import router as buyer_commodity_repertory_statistics_router
from routes.buyer_commofity_inventory_change import router as buyer_commodity_inventory_change_router


from routes.manage_sign_in import router as manage_sign_in_router
from routes.management_verify import router as management_verify_router
from routes.management_mall_info import router as management_mall_info_router
from routes.manage_merchant_freeze import router as manage_merchant_freeze_router
from routes.manage_merchant_unfreeze import router as manage_merchant_unfreeze_router
from routes.manage_merchant_delete import router as manage_merchant_delete_router
from routes.manage_get_commoidt_apply_list import router as manage_get_commoidt_apply_list_router
from routes.manage_get_commoidt_apply import router as manage_get_commoidt_apply_router
from routes.manage_commodity_rejectAudit import router as manage_commodity_rejectAudit_router
from routes.manage_commodity_passAudit import router as manage_commodity_passAudit_router

from routes.user_list import router as user_list_router
from routes.today_user_list import router as today_user_list_router
from routes.number_merchants import router as number_merchants_router
from routes.get_apply_seller_list import router as get_apply_seller_list_router
from routes.get_name_apply_seller_user import router as get_name_apply_seller_user_router
from routes.apply_seller_consent import router as apply_seller_consent_router
from routes.apply_seller_reject import router as apply_seller_reject_router
from routes.address_show import router as address_show_router
from routes.delete_token_time import router as delete_token_time_router
from routes.cs import router as cs_router
from services.bloom_filter_manager import init_bloom_filter_manager

redis_client = RedisClient()
scheduler = AsyncIOScheduler()

# ---------------------- 定时任务----------------------

async def rebuild_bloom_filters():
    """
    每小时重建布隆过滤器，从数据库加载所有需要的ID
    """
    try:
        logger.info("开始执行布隆过滤器重建任务...")
        
        from services.bloom_filter_manager import get_bloom_filter_manager
        bloom_manager = get_bloom_filter_manager()
        
        if not bloom_manager:
            logger.warning("布隆过滤器管理器未初始化，跳过重建任务")
            return
        
        async def load_all_ids():
            """从数据库加载所有需要加入布隆过滤器的ID"""
            mall_ids = []
            
            stores = await db_pool.execute_query("SELECT DISTINCT mall_id FROM store WHERE mall_id IS NOT NULL")
            mall_ids.extend([f"mall:{row[0]}" for row in stores if row[0] is not None])
            
            user_stores = await db_pool.execute_query("SELECT DISTINCT user FROM store WHERE user IS NOT NULL")
            mall_ids.extend([f"mall:user:{row[0]}" for row in user_stores if row[0] is not None])
            
            logger.info(f"从数据库加载了 {len(mall_ids)} 个ID用于布隆过滤器")
            return mall_ids
        
        await bloom_manager.rebuild_from_database(load_all_ids)
        logger.info("布隆过滤器重建任务完成")
        
    except Exception as e:
        logger.error(f"布隆过滤器重建任务失败: {str(e)}", exc_info=True)


async def user_sql_redis_state():
    """
    定时任务：清理离线用户的Redis在线状态缓存
    每10秒执行一次，同步数据库中的用户状态，删除已离线用户的Redis键
    目的：防止Redis中积累过多无效的在线状态数据
    """
    start_time = time.time()
    try:
        # 查询主商户表中状态不为1（已离线）的用户
        user_state_data1 = await db_pool.execute_query(
            'select user,mall_state from mall_info where mall_state != 1')
        # 查询店铺用户表中状态不为1（已离线）的用户
        user_state_data2 = await db_pool.execute_query(
            'select store_id,user,state from store_user where state != 1')
        
        # 收集需要删除的Redis键
        redis_keys_to_delete = []
        
        # 主商户Redis键格式：buyer_{用户名}
        if user_state_data1:
            for user, mall_state in user_state_data1:
                redis_keys_to_delete.append(f"buyer_{user}")
        
        # 店铺用户Redis键格式：buyer_{店铺ID}_{用户名}
        if user_state_data2:
            for store_id, user, state in user_state_data2:
                redis_keys_to_delete.append(f"buyer_{store_id}_{user}")
        
        # 批量删除Redis键，清理离线用户的状态缓存
        deleted_count = 0
        if redis_keys_to_delete:
            logger.info(f"定时任务: 发现 {len(redis_keys_to_delete)} 个需要清理的Redis键")
            for key in redis_keys_to_delete:
                try:
                    result = await redis_client.delete(key)
                    if result:
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"定时任务: 删除Redis键失败 | Key: {key} | 错误: {str(e)}")
        
        # 记录执行时间
        execution_time = time.time() - start_time
        query_count1 = len(user_state_data1) if user_state_data1 else 0
        query_count2 = len(user_state_data2) if user_state_data2 else 0
        
        if execution_time > 1.0:  # 如果执行时间超过1秒，记录警告
            logger.warning(
                f"用户状态同步任务执行时间较长: {execution_time:.2f}秒 | "
                f"查询mall_info记录数: {query_count1} | "
                f"查询store_user记录数: {query_count2} | "
                f"删除Redis键数: {deleted_count}"
            )
        elif execution_time > 0.1:  # 正常执行时间超过0.1秒也记录
            logger.info(
                f"用户状态同步任务执行完成: {execution_time:.2f}秒 | "
                f"查询mall_info记录数: {query_count1} | "
                f"查询store_user记录数: {query_count2} | "
                f"删除Redis键数: {deleted_count}"
            )
        else:
            # 快速执行时也记录关键信息
            logger.debug(
                f"用户状态同步任务快速完成: {execution_time:.3f}秒 | "
                f"删除Redis键数: {deleted_count}"
            )
            
    except asyncio.CancelledError:
        # 任务被取消时（如应用关闭），记录日志但不抛出异常
        execution_time = time.time() - start_time
        logger.info(f"用户状态同步任务被取消（可能是应用正在关闭）| 已执行时间: {execution_time:.2f}秒")
        raise  # 重新抛出 CancelledError，让调度器知道任务被取消
    except Exception as e:
        import traceback
        execution_time = time.time() - start_time
        error_traceback = traceback.format_exc()
        logger.error("=" * 60)
        logger.error(f"用户状态同步任务执行失败 | 执行时间: {execution_time:.2f}秒")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误信息: {str(e)}")
        logger.error(f"错误堆栈:\n{error_traceback}")
        logger.error("=" * 60)
    

# 定义 lifespan 事件处理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理，处理启动和关闭事件。
    在应用启动时连接 Redis ，MongoDB ，验证码Redis客户端，数据库连接池，关闭时断开连接。
    """
    # 应用启动信息（延迟写入，避免触发热重载）
    # 使用 asyncio.sleep(0.1) 延迟写入，确保应用已完全启动
    await asyncio.sleep(0.1)
    logger.info("=" * 60)
    logger.info("应用启动中...")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"运行平台: {sys.platform}")
    logger.info(f"工作目录: {os.getcwd()}")
    logger.info(f"进程ID: {os.getpid()}")
    
    # 检查虚拟环境
    python_path = sys.executable
    venv_env = os.environ.get('VIRTUAL_ENV')
    is_venv = venv_env is not None or sys.prefix != sys.base_prefix
    logger.info(f"Python解释器路径: {python_path}")
    if is_venv:
        logger.info(f"[虚拟环境] 已激活 | 路径: {venv_env if venv_env else sys.prefix}")
    else:
        logger.warning(f"[虚拟环境] 未检测到虚拟环境 | 建议激活虚拟环境后再运行")
    
    # 应用启动时的逻辑
    try:
        logger.info("正在连接Redis...")
        await redis_client.connect()
        logger.info(f"Redis 连接已建立 | URL: {redis_client.redis_url} | DB: {redis_client.db}")
        
        logger.info("正在连接MongoDB...")
        await mongodb_client.connect()
        logger.info(f"MongoDB 连接已建立 | URL: {mongodb_settings.MONGODB_URL}")
        
        logger.info("正在连接验证码Redis客户端...")
        await verifier.connect()
        logger.info("验证码Redis客户端连接已建立")
        
        logger.info("正在创建数据库连接池...")
        await db_pool.create_pool()
        logger.info(f"数据库连接池已创建 | 配置: {sql_settings.DATABASE_URL}")
        
        # 初始化布隆过滤器管理器
        logger.info("正在初始化布隆过滤器管理器...")
        from services.bloom_filter_manager import init_bloom_filter_manager
        bloom_filter_manager = init_bloom_filter_manager(redis_client)
        logger.info("布隆过滤器管理器已初始化")
        
        # 定时任务
        logger.info("正在配置定时任务...")
        scheduler.add_job(
            user_sql_redis_state, 
            IntervalTrigger(seconds=10),
            id='user_sql_redis_state',
            max_instances=1, 
            coalesce=True,    
            misfire_grace_time=30  
        )
        
        # 每小时重建布隆过滤器
        scheduler.add_job(
            rebuild_bloom_filters,
            IntervalTrigger(hours=1),
            id='rebuild_bloom_filters',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60
        )
        logger.info("每小时布隆过滤器重建任务已配置")
        
        scheduler.start()
        logger.info("定时任务已启动 | 任务ID: user_sql_redis_state | 执行间隔: 10秒")
        logger.info("定时任务已启动 | 任务ID: rebuild_bloom_filters | 执行间隔: 1小时")
        logger.info("=" * 60)
        logger.info("应用启动完成，所有服务已就绪")
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"应用启动失败: {str(e)}")
        logger.error("=" * 60)
        logger.error(f"应用启动失败: {str(e)}")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误详情:\n{error_traceback}")
        logger.error("=" * 60)
        raise
    
    # yield 之后是关闭逻辑
    yield
    
    # 应用关闭时的逻辑
    logger.info("=" * 60)
    logger.info("应用正在关闭，清理资源...")
    
    # 关闭定时任务：等待正在运行的任务完成
    try:
        scheduler.shutdown(wait=True)
        logger.info("定时任务已停止-用户状态检测")
    except asyncio.CancelledError:
        logger.info("定时任务关闭被取消（应用正在关闭）")
    except Exception as e:
        logger.warning(f"关闭定时任务时出错: {str(e)}")
    
    try:
        await redis_client.close()
        logger.info("Redis 连接已关闭")
    except asyncio.CancelledError:
        logger.info("Redis 连接关闭被取消")
    except Exception as e:
        logger.error(f"关闭Redis连接时出错: {str(e)}")
    
    try:
        await mongodb_client.close()
        logger.info("MongoDB 连接已关闭")
    except asyncio.CancelledError:
        logger.info("MongoDB 连接关闭被取消")
    except Exception as e:
        logger.error(f"关闭MongoDB连接时出错: {str(e)}")
    
    try:
        await verifier.close()
        logger.info("验证码Redis客户端连接已关闭")
    except asyncio.CancelledError:
        logger.info("验证码Redis客户端连接关闭被取消")
    except Exception as e:
        logger.error(f"关闭验证码Redis客户端连接时出错: {str(e)}")
    
    try:
        await db_pool.close_pool()
        logger.info("数据库连接池已关闭")
    except asyncio.CancelledError:
        logger.info("数据库连接池关闭被取消")
    except Exception as e:
        logger.error(f"关闭数据库连接池时出错: {str(e)}")
    
    logger.info("=" * 60)
    logger.info("应用已完全关闭")

logger = logging.getLogger("fastapi_logger")
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

# 标识中间件
class FastAPIIndicatorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # 添加FastAPI标识头
        response.headers["X-Powered-By"] = "FastAPI"
        # 可选：添加版本信息
        response.headers["Server"] = "FastAPI/0.115.0"  # 替换为你的FastAPI版本
        return response
app.add_middleware(FastAPIIndicatorMiddleware)
# 邮箱配置
email_config = {
    "sender_email": "3574747175@qq.com",
    "sender_password": "dusbvohhfaiucifi",
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "use_ssl": True
}


# 日志中间件
@app.middleware("http")
async def log_middleware(request: Request, call_next):
    # 请求日志
    start_time = time.time()
    client_ip = request.client.host if request.client else "Unknown"
    client_port = request.client.port if request.client else None
    
    # 获取请求参数
    query_params = dict(request.query_params) if request.query_params else {}
    
    # 获取User-Agent和Referer（有用的请求头信息）
    user_agent = request.headers.get('user-agent', 'N/A')
    referer = request.headers.get('referer', 'N/A')
    content_type = request.headers.get('content-type', 'N/A')
    
    logger.info(
        f"请求接收 | "
        f"方法: {request.method} | "
        f"路径: {request.url.path} | "
        f"查询参数: {query_params if query_params else '无'} | "
        f"客户端IP: {client_ip}:{client_port} | "
        f"Content-Type: {content_type} | "
        f"User-Agent: {user_agent[:100]} | "
        f"Referer: {referer[:100]}"
    )
    
    # 处理请求
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 获取响应大小
        response_body_size = 0
        if hasattr(response, 'body'):
            try:
                response_body_size = len(response.body) if response.body else 0
            except:
                pass
        
        # 响应日志
        log_level = logger.warning if process_time > 1.0 else logger.info
        log_level(
            f"请求完成 | "
            f"方法: {request.method} | "
            f"路径: {request.url.path} | "
            f"状态码: {response.status_code} | "
            f"处理时间: {process_time:.4f}秒 | "
            f"响应大小: {response_body_size} 字节 | "
            f"客户端IP: {client_ip}"
        )
        
        return response
        
    except Exception as e:
        import traceback
        process_time = time.time() - start_time
        error_traceback = traceback.format_exc()
        
        logger.error("=" * 60)
        logger.error(
            f"请求处理异常 | "
            f"方法: {request.method} | "
            f"路径: {request.url.path} | "
            f"处理时间: {process_time:.4f}秒 | "
            f"客户端IP: {client_ip}"
        )
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误信息: {str(e)}")
        logger.error(f"错误堆栈:\n{error_traceback}")
        logger.error("=" * 60)
        
        # 返回错误响应
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# 创建全局验证码实例（使用配置文件中的Redis配置）
verifier = VerificationCode(
    redis_url=redis_settings.REDIS_URL, 
    db=redis_settings.REDIS_DB,
    email_config=email_config
)
fastapi_cdn_host.patch_docs(app)

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

# 买家端token路由
app.include_router(buyer_side_token_router,prefix='/api')

# 买家端登录路由
app.include_router(buyer_side_sgin_router,prefix='/api')

# 管理员登录路由
app.include_router(manage_sign_in_router,prefix='/api')

# 管理员验证路由
app.include_router(management_verify_router,prefix='/api')

# 管理员获取商品申请路由
app.include_router(manage_get_commoidt_apply_list_router,prefix='/api')

# 管理员驳回商品上架申请路由
app.include_router(manage_commodity_rejectAudit_router,prefix='/api')

# 管理员获取商品上架申请详情路由
app.include_router(manage_get_commoidt_apply_router,prefix='/api')

# 管理员通过商品上架申请路由
app.include_router(manage_commodity_passAudit_router,prefix='/api')

# 冻结商家路由
app.include_router(manage_merchant_freeze_router,prefix='/api')

# 解冻商家路由
app.include_router(manage_merchant_unfreeze_router,prefix='/api')

# 删除商家路由
app.include_router(manage_merchant_delete_router,prefix='/api')

# 删除token时间戳路由
app.include_router(delete_token_time_router,prefix='/api')

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

# 买家端重复店铺检测路由
app.include_router(buyer_repeat_show_router,prefix='/api')

# 店铺图片上传路由
app.include_router(mall_img_upload_router,prefix='/api')

# 店铺添加路由
app.include_router(add_mall_router,prefix='/api')

# 买家端获取店铺名称路由
app.include_router(buyer_get_mall_name_router,prefix='/api')

# 买家端删除店铺路由
app.include_router(buyer_delete_show_router,prefix='/api')

# 买家端获取店铺信息路由
app.include_router(buyer_get_mall_info_router,prefix='/api')

# 买家端修改店铺路由
app.include_router(buyer_update_mall_router,prefix='/api')

# 买家端上传商品图片路由
app.include_router(buyer_img_update_router,prefix='/api')

# 买家端获取店铺用户列表路由
app.include_router(buyer_mall_user_list_router,prefix='/api')

# 买家端添加用户路由
app.include_router(buyer_user_add_router,prefix='/api')

# 买家端上传用户头像路由
app.include_router(buyer_user_picture_uploading_router,prefix='/api')

# 买家端选择用户筛选
app.include_router(buyer_user_select_router,prefix='/api')

# 买家端删除用户路由
app.include_router(buyer_user_delete_router,prefix='/api')

# 买家端修改用户路由
app.include_router(buyer_amend_user_router,prefix='/api')

# 买家端获取用户角色路由
app.include_router(buyer_get_role_router,prefix='/api')

# 买家端获取角色操作码路由
app.include_router(buter_role_code_get_router,prefix='/api')

# 买家端添加角色路由
app.include_router(buyer_role_add_router,prefix='/api')

# 买家端删除角色路由
app.include_router(buyter_delete_role_router,prefix='/api')

# 买家端获取角色信息路由
app.include_router(buyer_role_info_router,prefix='/api')

# 买家端更新角色路由
app.include_router(buyer_update_role_router,prefix='/api')

# 买家端角色比例路由
app.include_router(buyer_role_ratio_router,prefix='/api')

# 获取分类路由
app.include_router(get_classify_router,prefix='/api')

# 买家端获取商品路由
app.include_router(buyer_get_commoidt_router,prefix='/api')

# 买家端获取商品通知路由
app.include_router(buyer_commodity_inform_router,prefix='/api')

# 买家端标记商品通知为已读路由
app.include_router(buyer_r_commodity_inform_read_router,prefix='/api')

# 买家端删除商品通知路由
app.include_router(buyer_commodity_inform_delete_router,prefix='/api')

# 商品添加路由
app.include_router(buyer_commoidt_add_router,prefix='/api')

# 商品编辑路由
app.include_router(buyer_commodity_edit_router,prefix='/api')

# 买家端删除商品路由
app.include_router(buyer_commodity_delete_router,prefix='/api')

# 买家端下架商品路由
app.include_router(buyer_commodity_delisting_router,prefix='/api')

# 买家端上架商品路由
app.include_router(buyer_commodity_putaway_router,prefix='/api')

# 买家端新增分类路由
app.include_router(buyer_classify_add_router,prefix='/api')

# 买家端删除分类路由
app.include_router(buyer_classify_delete_router,prefix='/api')

# 买家端修改分类路由
app.include_router(buyer_classify_edit_router,prefix='/api')

# 买家端商品库存列表路由
app.include_router(buyer_commodity_repertory_list_router,prefix='/api')

# 买家端商品库存统计路由
app.include_router(buyer_commodity_repertory_statistics_router,prefix='/api')

# 买家端商品库存变化路由
app.include_router(buyer_commodity_inventory_change_router,prefix='/api')

# cs路由
app.include_router(cs_router,prefix='/api')