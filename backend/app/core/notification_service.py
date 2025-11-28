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

    def __init__(self, bark_url: str = None, email_config: dict = None, push_projects: str = 'all', push_types: str = 'all'):
        """
        初始化通知服务
        
        Args:
            bark_url: Bark服务器URL
            email_config: 邮件配置，包含smtp_server, smtp_port, username, password, from_email
            push_projects: 推送项目，可选值：all, customers, cdrs, phones, gateways
            push_types: 推送类型，可选值：all, success, error
        """
        self.bark_url = bark_url
        self.email_config = email_config
        self.push_projects = push_projects
        self.push_types = push_types

    def send_notification(self, title: str, content: str, notification_type: str = "all", project_type: str = "all", result_type: str = "success"):
        """
        发送通知
        
        Args:
            title: 通知标题
            content: 通知内容
            notification_type: 通知类型，可选值：all, bark, email
            project_type: 项目类型，可选值：all, customers, cdrs, phones, gateways
            result_type: 结果类型，可选值：success, error
        """
        # 检查推送项目是否匹配
        if self.push_projects != 'all' and project_type != self.push_projects:
            logger.debug(f"跳过通知: 项目类型 {project_type} 不在配置的推送项目 {self.push_projects} 中")
            return
        
        # 检查推送类型是否匹配
        if self.push_types != 'all' and result_type != self.push_types:
            logger.debug(f"跳过通知: 结果类型 {result_type} 不在配置的推送类型 {self.push_types} 中")
            return
        
        # 发送Bark通知
        if notification_type in ["all", "bark"] and self.bark_url:
            try:
                self._send_bark_notification(title, content)
            except Exception as e:
                logger.error(f"发送Bark通知失败: {e}")

        # 发送邮件通知
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

            # 发送邮件，添加超时和重试机制
            server = None
            try:
                server = smtplib.SMTP(self.email_config.get('smtp_server'), self.email_config.get('smtp_port'), timeout=15)
                server.starttls()
                server.login(self.email_config.get('username'), self.email_config.get('password'))
                server.send_message(msg)
                logger.info(f"邮件通知发送成功: {title}")
            except smtplib.SMTPServerDisconnected as e:
                logger.error(f"邮件服务器连接断开: {e}")
                # 不抛出异常，避免影响其他功能
            except smtplib.SMTPException as e:
                logger.error(f"SMTP错误: {e}")
                # 不抛出异常，避免影响其他功能
            except Exception as e:
                logger.error(f"发送邮件通知失败: {e}")
                # 不抛出异常，避免影响其他功能
            finally:
                if server:
                    try:
                        server.quit()
                    except:
                        pass
        except Exception as e:
            logger.error(f"邮件发送过程中发生错误: {e}")
            # 不抛出异常，避免影响其他功能


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

    # 检查所有必要配置是否存在且非空
    if all([
        smtp_server and smtp_server.config_value and smtp_server.config_value.strip(),
        smtp_port and smtp_port.config_value and smtp_port.config_value.strip(),
        username and username.config_value and username.config_value.strip(),
        password and password.config_value and password.config_value.strip(),
        from_email and from_email.config_value and from_email.config_value.strip(),
        to_email and to_email.config_value and to_email.config_value.strip()
    ]):
        try:
            email_config = {
                'smtp_server': smtp_server.config_value,
                'smtp_port': int(smtp_port.config_value),
                'username': username.config_value,
                'password': password.config_value,
                'from_email': from_email.config_value,
                'to_email': to_email.config_value
            }
        except ValueError as e:
            logger.error(f'邮件配置解析失败: {e}')
            email_config = None

    # 获取推送项目和类型配置
    push_projects = 'all'
    push_projects_config = db.query(AppConfig).filter(AppConfig.config_key == 'notification_push_projects').first()
    if push_projects_config and push_projects_config.config_value:
        push_projects = push_projects_config.config_value

    push_types = 'all'
    push_types_config = db.query(AppConfig).filter(AppConfig.config_key == 'notification_push_types').first()
    if push_types_config and push_types_config.config_value:
        push_types = push_types_config.config_value

    return NotificationService(
        bark_url=bark_url, 
        email_config=email_config,
        push_projects=push_projects,
        push_types=push_types
    )