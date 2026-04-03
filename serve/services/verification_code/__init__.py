import asyncio
import random
import time
import smtplib
import logging
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from typing import Tuple, Optional
from data.redis_client import RedisClient

logger = logging.getLogger(__name__)


class VerificationCode:
    def __init__(self, redis_url: str = "redis://localhost", db: int = 0,
                 expiry: int = 300, cooldown: int = 60,
                 email_config: dict = None, mongo=None):
        self.expiry = expiry
        self.cooldown = cooldown
        self.redis_client = RedisClient(redis_url, db)
        self.mongo = mongo
        self._fallback_email_config = email_config or {}

    async def _load_email_config(self) -> dict:
        """从 MongoDB 动态加载邮件配置，不存在则回退到初始化配置。"""
        if self.mongo:
            try:
                doc = await self.mongo.find_one("EmailServiceConfig", {})
                if doc:
                    return {
                        "sender_email": doc.get("sender_email", ""),
                        "sender_password": doc.get("sender_password", ""),
                        "smtp_server": doc.get("smtp_server", ""),
                        "smtp_port": int(doc.get("smtp_port", 465)),
                        "use_ssl": doc.get("use_ssl", True),
                        "sender_name": doc.get("sender_name", "系统通知"),
                    }
            except Exception as e:
                logger.warning("从 MongoDB 加载邮件配置失败，使用回退配置: %s", e)
        return self._fallback_email_config

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
        为指定用户生成并存储验证码（使用Redis Pipeline优化性能）
        
        Returns:
            (是否成功, 验证码, 剩余冷却时间)
        """
        can_generate, remaining = await self.can_generate_code(user_id)
        
        if not can_generate:
            return False, None, remaining
            
        code = self.generate_code()
        
        # 使用Redis Pipeline批量执行命令，减少网络往返次数
        # 同时存储验证码和最后生成时间，保证原子性操作
        commands = [
            ("setex", (user_id, self.expiry, code)),  # 验证码，5分钟过期
            ("setex", (f"{user_id}:last_generated", self.cooldown, str(time.time())))  # 冷却时间记录，1分钟过期
        ]
        await self.redis_client.execute_pipeline(commands)
        
        return True, code, 0

    async def verify_code(self, user_id: str, code: str) -> bool:
        """
        验证用户输入的验证码
        验证成功后立即删除，确保验证码只能使用一次（防止重放攻击）
        """
        stored_code = await self.redis_client.get(user_id)
        if stored_code and stored_code == code:
            await self.redis_client.delete(user_id)  # 一次性使用，验证后立即删除
            return True
        return False

    async def get_remaining_time(self, user_id: str) -> int:
        """获取验证码的剩余有效时间（秒）"""
        return await self.redis_client.get_ttl(user_id)
    
    async def send_email(self, receiver_email: str, code: str) -> bool:
        """异步发送验证码邮件，每次发送前从 MongoDB 加载最新配置。"""
        try:
            cfg = await self._load_email_config()
            if not cfg.get("sender_email") or not cfg.get("smtp_server"):
                logger.error("邮件配置不完整，无法发送")
                return False
            return await asyncio.to_thread(self._send_email_sync, receiver_email, code, cfg)
        except smtplib.SMTPAuthenticationError:
            logger.error("邮箱登录失败，请检查邮箱地址和授权码")
            return False
        except smtplib.SMTPServerDisconnected:
            logger.error("SMTP 服务器断开连接，请检查网络")
            return False
        except smtplib.SMTPException as e:
            logger.error("SMTP 通信错误：%s", e)
            return False
        except Exception as e:
            logger.error("发送邮件未知错误：%s", e)
            return False

    def _send_email_sync(self, receiver_email: str, code: str, cfg: dict) -> bool:
        sender_email = cfg.get("sender_email")
        sender_password = cfg.get("sender_password")
        smtp_server = cfg.get("smtp_server")
        smtp_port = cfg.get("smtp_port", 465)
        use_ssl = cfg.get("use_ssl", True)
        sender_name = cfg.get("sender_name", "系统通知")

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
        message['From'] = formataddr((sender_name, sender_email))
        message['To'] = formataddr((receiver_email.split('@')[0], receiver_email))
        message['Subject'] = Header(subject, 'utf-8')

        server = None
        try:
            logger.info("连接 SMTP 服务器：%s:%s", smtp_server, smtp_port)
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
            server.set_debuglevel(0)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            server.quit()
            logger.info("邮件发送成功 -> %s", receiver_email)
            return True
        except smtplib.SMTPAuthenticationError:
            raise
        except smtplib.SMTPServerDisconnected:
            raise
        except smtplib.SMTPException:
            raise
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

    async def verify_smtp_connection(self) -> dict:
        """测试 SMTP 连通性，不实际发送邮件。"""
        cfg = await self._load_email_config()
        if not cfg.get("sender_email") or not cfg.get("smtp_server"):
            return {"success": False, "msg": "邮件配置不完整，请先填写完整配置"}
        try:
            result = await asyncio.to_thread(self._verify_smtp_sync, cfg)
            return result
        except Exception as e:
            return {"success": False, "msg": f"连接失败：{str(e)}"}

    @staticmethod
    def _verify_smtp_sync(cfg: dict) -> dict:
        smtp_server = cfg.get("smtp_server")
        smtp_port = cfg.get("smtp_port", 465)
        use_ssl = cfg.get("use_ssl", True)
        sender_email = cfg.get("sender_email")
        sender_password = cfg.get("sender_password")
        server = None
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                server.starttls()
            server.login(sender_email, sender_password)
            server.quit()
            return {"success": True, "msg": f"SMTP 连接成功（{smtp_server}:{smtp_port}）"}
        except smtplib.SMTPAuthenticationError:
            return {"success": False, "msg": "认证失败：邮箱地址或授权码不正确"}
        except smtplib.SMTPServerDisconnected:
            return {"success": False, "msg": f"无法连接到 {smtp_server}:{smtp_port}，请检查服务器地址和端口"}
        except smtplib.SMTPException as e:
            return {"success": False, "msg": f"SMTP 协议错误：{str(e)}"}
        except OSError as e:
            return {"success": False, "msg": f"网络错误：{str(e)}"}
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

    async def send_verification_email(self, user_id: str, email: str) -> Tuple[bool, int]:
        success, code, remaining = await self.send_code(user_id)
        if not success:
            return False, remaining
        email_success = await self.send_email(email, code)
        return email_success, 0