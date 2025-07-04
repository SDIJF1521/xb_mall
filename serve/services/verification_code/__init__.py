import asyncio
import random
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from typing import Tuple, Optional
from data.redis_client import RedisClient  # 假设两个文件在同一目录


class VerificationCode:
    def __init__(self, redis_url: str = "redis://localhost", db: int = 0, 
                 expiry: int = 300, cooldown: int = 60, email_config: dict = None):
        """
        初始化验证码系统（支持异步邮件发送和Redis缓存）
        
        Args:
            redis_url: Redis连接URL
            db: Redis数据库编号
            expiry: 验证码过期时间（秒），默认5分钟
            cooldown: 验证码生成冷却时间（秒），默认1分钟
            email_config: 邮箱配置，包含sender_email, sender_password等
        """
        self.expiry = expiry
        self.cooldown = cooldown
        self.redis_client = RedisClient(redis_url, db)
        
        # 默认邮箱配置（建议通过环境变量或配置文件加载）
        self.email_config = email_config or {
            "sender_email": "3574747175@qq.com",
            "sender_password": "dusbvohhfaiucifi",
            "smtp_server": "smtp.qq.com",
            "smtp_port": 465,
            "use_ssl": True
        }

    async def connect(self) -> None:
        """异步连接到Redis服务器"""
        await self.redis_client.connect()

    async def close(self) -> None:
        """异步关闭Redis连接"""
        await self.redis_client.close()

    def generate_code(self, length: int = 6) -> str:
        """生成指定长度的随机数字验证码（使用secrets增强安全性）"""
        return ''.join(random.choices('0123456789', k=length))

    async def can_generate_code(self, user_id: str) -> Tuple[bool, int]:
        """
        检查用户是否可以生成新的验证码
        
        Returns:
            (是否可以生成, 剩余冷却时间)
        """
        last_generated = await self.redis_client.get(f"{user_id}:last_generated")
        
        if not last_generated:
            return True, 0
            
        current_time = time.time()
        last_time = float(last_generated)
        
        if current_time - last_time >= self.cooldown:
            return True, 0
        else:
            remaining = int(self.cooldown - (current_time - last_time))
            return False, remaining
        
        
    async def send_code(self, user_id: str) -> Tuple[bool, Optional[str], int]:
        """
        为指定用户生成并存储验证码（使用Redis Pipeline优化）
        
        Returns:
            (是否成功, 验证码, 剩余冷却时间)
        """
        can_generate, remaining = await self.can_generate_code(user_id)
        
        if not can_generate:
            return False, None, remaining
            
        code = self.generate_code()
        
        # 使用Pipeline批量执行Redis命令
        commands = [
            ("setex", (user_id, self.expiry, code)),
            ("setex", (f"{user_id}:last_generated", self.cooldown, str(time.time())))
        ]
        await self.redis_client.execute_pipeline(commands)  # 调用新方法
        
        return True, code, 0

    async def verify_code(self, user_id: str, code: str) -> bool:
        """验证用户输入的验证码（验证后删除防止重复使用）"""
        stored_code = await self.redis_client.get(user_id)
        if stored_code and stored_code == code:
            await self.redis_client.delete(user_id)  # 一次性使用
            return True
        return False

    async def get_remaining_time(self, user_id: str) -> int:
        """获取验证码的剩余有效时间（秒）"""
        return await self.redis_client.get_ttl(user_id)
    
    async def send_email(self, receiver_email: str, code: str) -> bool:
        """
        异步发送验证码邮件
        """
        try:
            # 通过线程池执行同步邮件发送，避免阻塞事件循环
            return await asyncio.to_thread(
                self._send_email_sync,
                receiver_email,
                code
            )
        except smtplib.SMTPAuthenticationError:
            print("错误：邮箱登录失败，请检查邮箱地址和授权码是否正确")
            return False
        except smtplib.SMTPServerDisconnected:
            print("错误：SMTP服务器断开连接，请检查网络连接")
            return False
        except smtplib.SMTPException as e:
            print(f"SMTP通信错误：{str(e)}")
            return False
        except Exception as e:
            print(f"发送邮件未知错误：{str(e)}")
            return False

    def _send_email_sync(self, receiver_email: str, code: str) -> bool:
        """
        同步发送邮件的核心逻辑
        """
        # 从配置中获取邮箱信息
        sender_email = self.email_config.get("sender_email")
        sender_password = self.email_config.get("sender_password")
        smtp_server = self.email_config.get("smtp_server")
        smtp_port = self.email_config.get("smtp_port")
        use_ssl = self.email_config.get("use_ssl", True)
        
        # 构造HTML格式邮件内容
        subject = "【系统通知】验证码"
        content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="border: 1px solid #eaeaea; border-radius: 8px; padding: 20px;">
                <h3 style="color: #333; margin-top: 0;">您的验证码是：<strong style="font-size: 1.5em;">{code}</strong></h3>
                <p style="color: #666;">该验证码 <strong>5 分钟</strong> 内有效，请及时输入。</p>
                <p style="color: #999; font-size: 0.9em; margin-bottom: 0;">如非本人操作，请忽略此邮件。</p>
            </div>
        </body>
        </html>
        """
        message = MIMEText(content, 'html', 'utf-8')
        
        # 设置邮件头信息
        message['From'] = formataddr(("系统通知", sender_email))
        receiver_name = receiver_email.split('@')[0]
        message['To'] = formataddr((receiver_name, receiver_email))
        message['Subject'] = Header(subject, 'utf-8')
        
        # 连接SMTP服务器并发送邮件
        server = None
        try:
            print(f"正在连接SMTP服务器：{smtp_server}:{smtp_port}")
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()  # 启用TLS加密
                
            server.set_debuglevel(0)  # 生产环境关闭调试日志
            
            print("正在登录邮箱...")
            server.login(sender_email, sender_password)
            
            print(f"正在发送邮件到 {receiver_email}...")
            server.sendmail(sender_email, receiver_email, message.as_string())
            
            server.quit()
            print("邮件发送成功！")
            return True
            
        except smtplib.SMTPAuthenticationError:
            # 邮箱账号或授权码错误
            raise smtplib.SMTPAuthenticationError("邮箱登录失败，请检查邮箱地址和授权码")
        except smtplib.SMTPServerDisconnected:
            # 服务器连接断开
            raise smtplib.SMTPServerDisconnected("SMTP服务器连接断开，请检查网络")
        except smtplib.SMTPException as e:
            # 其他SMTP协议错误
            raise smtplib.SMTPException(f"SMTP协议错误：{str(e)}")
        finally:
            # 确保关闭连接
            if server:
                try:
                    server.quit()
                except:
                    pass

    async def send_verification_email(self, user_id: str, email: str) -> Tuple[bool, int]:
        """
        完整的验证码发送流程：
        1. 生成验证码并存储到Redis
        2. 检查冷却时间
        3. 异步发送邮件
        4. 返回操作结果和剩余时间
        """
        success, code, remaining = await self.send_code(user_id)
        
        if not success:
            return False, remaining
            
        # 异步发送邮件并返回结果
        email_success = await self.send_email(email, code)
        return email_success, 0