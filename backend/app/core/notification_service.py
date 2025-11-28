import logging
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationService:
    """
    通知服务，支持多种通知方式
    - Bark推送
    - 邮件推送
    """

    def __init__(self, bark_url: str = None, email_config: dict = None):
        """
        初始化通知服务
        
        Args:
            bark_url: Bark服务器URL
            email_config: 邮件配置，包含smtp_server, smtp_port, username, password, from_email
        """
        self.bark_url = bark_url
        self.email_config = email_config

    def send_notification(self, title: str, content: str, notification_type: str = "all"):
        """
        发送通知
        
        Args:
            title: 通知标题
            content: 通知内容
            notification_type: 通知类型，可选值：all, bark, email
        """
        if notification_type in ["all", "bark"] and self.bark_url:
            try:
                self._send_bark_notification(title, content)
            except Exception as e:
                logger.error(f"发送Bark通知失败: {e}")

        if notification_type in ["all", "email"] and self.email_config:
            try:
                self._send_email_notification(title, content)
            except Exception as e:
                logger.error(f"发送邮件通知失败: {e}")

    def _send_bark_notification(self, title: str, content: str):
        """
        发送Bark通知
        
        Args:
            title: 通知标题
            content: 通知内容
        """
        if not self.bark_url:
            logger.warning("Bark URL未配置，跳过发送Bark通知")
            return

        try:
            # Bark API格式：https://api.day.app/[key]/[title]/[content]
            # 或者：https://api.day.app/[key]?title=[title]&body=[content]
            url = f"{self.bark_url.rstrip('/')}/{title}/{content}"
            response = httpx.get(url, timeout=10)
            response.raise_for_status()
            logger.info(f"Bark通知发送成功: {title}")
        except httpx.RequestError as e:
            logger.error(f"发送Bark通知失败: {e}")
            raise

    def _send_email_notification(self, title: str, content: str):
        """
        发送邮件通知
        
        Args:
            title: 通知标题
            content: 通知内容
        """
        if not self.email_config:
            logger.warning("邮件配置未设置，跳过发送邮件通知")
            return

        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.email_config.get('from_email')
            msg['To'] = self.email_config.get('to_email')
            msg['Subject'] = title

            # 添加邮件正文
            msg.attach(MIMEText(content, 'plain', 'utf-8'))

            # 发送邮件
            with smtplib.SMTP(self.email_config.get('smtp_server'), self.email_config.get('smtp_port')) as server:
                server.starttls()
                server.login(self.email_config.get('username'), self.email_config.get('password'))
                server.send_message(msg)

            logger.info(f"邮件通知发送成功: {title}")
        except Exception as e:
            logger.error(f"发送邮件通知失败: {e}")
            raise


def get_notification_service(db):
    """
    从数据库获取通知配置并创建通知服务实例
    
    Args:
        db: 数据库会话
    
    Returns:
        NotificationService: 通知服务实例
    """
    from app.models.app_config import AppConfig

    # 获取Bark配置
    bark_url = None
    bark_config = db.query(AppConfig).filter(AppConfig.config_key == 'notification_bark_url').first()
    if bark_config and bark_config.config_value:
        bark_url = bark_config.config_value

    # 获取邮件配置
    email_config = None
    smtp_server = db.query(AppConfig).filter(AppConfig.config_key == 'notification_email_smtp_server').first()
    smtp_port = db.query(AppConfig).filter(AppConfig.config_key == 'notification_email_smtp_port').first()
    username = db.query(AppConfig).filter(AppConfig.config_key == 'notification_email_username').first()
    password = db.query(AppConfig).filter(AppConfig.config_key == 'notification_email_password').first()
    from_email = db.query(AppConfig).filter(AppConfig.config_key == 'notification_email_from').first()
    to_email = db.query(AppConfig).filter(AppConfig.config_key == 'notification_email_to').first()

    if all([smtp_server, smtp_port, username, password, from_email, to_email]):
        email_config = {
            'smtp_server': smtp_server.config_value,
            'smtp_port': int(smtp_port.config_value),
            'username': username.config_value,
            'password': password.config_value,
            'from_email': from_email.config_value,
            'to_email': to_email.config_value
        }

    return NotificationService(bark_url=bark_url, email_config=email_config)