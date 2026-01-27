"""
邮件发送服务

支持通过SMTP发送邮件，用于发送验证码、密码重置链接等。
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Optional
import os

logger = logging.getLogger(__name__)


class EmailService:
    """邮件发送服务"""
    
    def __init__(
        self,
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        smtp_use_tls: bool = True,
        from_email: str = "",
        from_name: str = "AxiomFlow",
    ):
        """
        初始化邮件服务
        
        Args:
            smtp_host: SMTP服务器地址
            smtp_port: SMTP端口（通常587用于TLS，465用于SSL）
            smtp_user: SMTP用户名（通常是邮箱地址）
            smtp_password: SMTP密码或应用专用密码
            smtp_use_tls: 是否使用TLS（True使用587端口，False使用465端口需要SSL）
            from_email: 发件人邮箱
            from_name: 发件人名称
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_use_tls = smtp_use_tls
        self.from_email = from_email or smtp_user
        self.from_name = from_name
        self.enabled = bool(smtp_host and smtp_user and smtp_password)
    
    def send_verification_code(self, to_email: str, code: str) -> bool:
        """
        发送验证码邮件
        
        Args:
            to_email: 收件人邮箱
            code: 6位验证码
            
        Returns:
            是否发送成功
        """
        subject = "AxiomFlow 验证码 | 安全验证"
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
                    line-height: 1.7;
                    color: #1e293b;
                    background: linear-gradient(135deg, #f0f9ff 0%, #e0e7ff 50%, #f3e8ff 100%);
                    padding: 40px 20px;
                    min-height: 100vh;
                }}
                .email-wrapper {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: #ffffff;
                    border-radius: 24px;
                    box-shadow: 
                        0 20px 60px rgba(99, 102, 241, 0.15),
                        0 8px 24px rgba(99, 102, 241, 0.1),
                        0 0 0 1px rgba(255, 255, 255, 0.5) inset;
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
                    padding: 40px 32px;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                }}
                .header::before {{
                    content: '';
                    position: absolute;
                    top: -50%;
                    left: -50%;
                    width: 200%;
                    height: 200%;
                    background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
                    animation: shimmer 3s ease-in-out infinite;
                }}
                @keyframes shimmer {{
                    0%, 100% {{ transform: translate(-50%, -50%) rotate(0deg); }}
                    50% {{ transform: translate(-50%, -50%) rotate(180deg); }}
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: 800;
                    color: #ffffff;
                    letter-spacing: -0.02em;
                    margin-bottom: 8px;
                    position: relative;
                    z-index: 1;
                    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                }}
                .header-subtitle {{
                    font-size: 16px;
                    color: rgba(255, 255, 255, 0.95);
                    font-weight: 500;
                    position: relative;
                    z-index: 1;
                }}
                .content {{
                    padding: 48px 40px;
                    background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
                }}
                .greeting {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #1e293b;
                    margin-bottom: 16px;
                    letter-spacing: -0.01em;
                }}
                .description {{
                    font-size: 15px;
                    color: #64748b;
                    line-height: 1.8;
                    margin-bottom: 32px;
                }}
                .code-container {{
                    background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);
                    border: 2px solid rgba(99, 102, 241, 0.15);
                    border-radius: 20px;
                    padding: 32px 24px;
                    text-align: center;
                    margin: 32px 0;
                    box-shadow: 
                        0 8px 24px rgba(99, 102, 241, 0.1),
                        0 0 0 1px rgba(255, 255, 255, 0.5) inset;
                    position: relative;
                    overflow: hidden;
                }}
                .code-container::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
                    animation: slide 3s ease-in-out infinite;
                }}
                @keyframes slide {{
                    0% {{ left: -100%; }}
                    50%, 100% {{ left: 100%; }}
                }}
                .code-label {{
                    font-size: 13px;
                    color: #8b5cf6;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    margin-bottom: 16px;
                }}
                .code {{
                    font-size: 42px;
                    font-weight: 800;
                    letter-spacing: 0.3em;
                    font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    margin: 8px 0;
                    position: relative;
                    z-index: 1;
                    text-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
                }}
                .warning-box {{
                    background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(245, 158, 11, 0.08) 100%);
                    border: 1.5px solid rgba(251, 191, 36, 0.3);
                    border-radius: 16px;
                    padding: 20px 24px;
                    margin: 32px 0;
                    box-shadow: 0 4px 12px rgba(251, 191, 36, 0.1);
                }}
                .warning-title {{
                    font-size: 14px;
                    font-weight: 700;
                    color: #d97706;
                    margin-bottom: 8px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .warning-text {{
                    font-size: 14px;
                    color: #92400e;
                    line-height: 1.7;
                }}
                .info-section {{
                    margin-top: 40px;
                    padding-top: 32px;
                    border-top: 1px solid rgba(226, 232, 240, 0.8);
                }}
                .info-title {{
                    font-size: 15px;
                    font-weight: 600;
                    color: #334155;
                    margin-bottom: 16px;
                }}
                .info-list {{
                    list-style: none;
                    padding: 0;
                }}
                .info-item {{
                    font-size: 14px;
                    color: #64748b;
                    line-height: 1.8;
                    margin-bottom: 12px;
                    padding-left: 24px;
                    position: relative;
                }}
                .info-item::before {{
                    content: '✓';
                    position: absolute;
                    left: 0;
                    color: #10b981;
                    font-weight: bold;
                    font-size: 16px;
                }}
                .footer {{
                    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                    padding: 32px 40px;
                    text-align: center;
                    border-top: 1px solid rgba(226, 232, 240, 0.5);
                }}
                .footer-text {{
                    font-size: 13px;
                    color: #94a3b8;
                    line-height: 1.7;
                    margin-bottom: 12px;
                }}
                .footer-copyright {{
                    font-size: 12px;
                    color: #cbd5e1;
                    margin-top: 16px;
                    font-weight: 500;
                }}
                .divider {{
                    height: 1px;
                    background: linear-gradient(90deg, transparent, rgba(226, 232, 240, 0.8), transparent);
                    margin: 24px 0;
                }}
                @media only screen and (max-width: 600px) {{
                    .content {{
                        padding: 32px 24px;
                    }}
                    .code {{
                        font-size: 36px;
                        letter-spacing: 0.2em;
                    }}
                    .header {{
                        padding: 32px 24px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-wrapper">
                <div class="header">
                    <div class="logo">AxiomFlow</div>
                    <div class="header-subtitle">安全验证码</div>
                </div>
                
                <div class="content">
                    <div class="greeting">您好！</div>
                    
                    <div class="description">
                        我们收到了您的密码重置请求。为了确保账户安全，请使用以下验证码完成身份验证。
                    </div>
                    
                    <div class="code-container">
                        <div class="code-label">验证码</div>
                        <div class="code">{code}</div>
                        <div style="font-size: 12px; color: #94a3b8; margin-top: 12px; font-weight: 500;">
                            包含字母和数字，不区分大小写
                        </div>
                    </div>
                    
                    <div class="warning-box">
                        <div class="warning-title">
                            <span>⚠️</span>
                            <span>安全提示</span>
                        </div>
                        <div class="warning-text">
                            • 验证码有效期为 <strong>5分钟</strong>，请及时使用<br>
                            • 请勿将验证码泄露给他人，包括客服人员<br>
                            • 如非本人操作，请立即修改密码并联系客服
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <div class="info-title">💡 使用说明</div>
                        <ul class="info-list">
                            <li class="info-item">在密码重置页面输入上述6位验证码（字母+数字）</li>
                            <li class="info-item">验证码不区分大小写，可直接输入</li>
                            <li class="info-item">验证通过后即可设置新密码</li>
                            <li class="info-item">验证码仅可使用一次，使用后立即失效</li>
                        </ul>
                    </div>
                    
                    <div class="divider"></div>
                    
                    <div class="description" style="font-size: 13px; color: #94a3b8; margin-bottom: 0;">
                        如果您没有请求此验证码，请忽略此邮件。您的账户仍然安全，无需采取任何操作。
                    </div>
                </div>
                
                <div class="footer">
                    <div class="footer-text">
                        此邮件由 AxiomFlow 系统自动发送，请勿回复。
                    </div>
                    <div class="footer-copyright">
                        © 2024 AxiomFlow Team. All rights reserved.
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
AxiomFlow 安全验证码

您好！

我们收到了您的密码重置请求。为了确保账户安全，请使用以下验证码完成身份验证。

验证码：{code}

安全提示：
• 验证码有效期为 5分钟，请及时使用
• 请勿将验证码泄露给他人，包括客服人员
• 如非本人操作，请立即修改密码并联系客服

使用说明：
✓ 在密码重置页面输入上述6位验证码（字母+数字）
✓ 验证码不区分大小写，可直接输入
✓ 验证通过后即可设置新密码
✓ 验证码仅可使用一次，使用后立即失效

如果您没有请求此验证码，请忽略此邮件。您的账户仍然安全，无需采取任何操作。

此邮件由 AxiomFlow 系统自动发送，请勿回复。

© 2024 AxiomFlow Team. All rights reserved.
        """
        
        return self._send_email(to_email, subject, text_content, html_content)
    
    def _send_email(self, to_email: str, subject: str, text_content: str, html_content: str) -> bool:
        """
        发送邮件（内部方法）
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            text_content: 纯文本内容
            html_content: HTML内容
            
        Returns:
            是否发送成功
        """
        if not self.enabled:
            logger.warning(f"邮件服务未启用，跳过发送邮件到 {to_email}")
            return False
        
        try:
            # 创建邮件消息
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{Header(self.from_name, 'utf-8')} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 添加文本和HTML内容
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)
            
            # 连接SMTP服务器并发送
            # 设置超时时间（秒）
            timeout = 30
            server = None
            
            try:
                # 确保使用完整的邮箱地址作为用户名（QQ邮箱要求）
                login_user = self.smtp_user
                if "@" not in login_user and "@" in self.from_email:
                    # 如果smtp_user不是邮箱格式，但from_email是，使用from_email
                    login_user = self.from_email
                elif "@" not in login_user:
                    # 如果都不是邮箱格式，尝试从smtp_host推断（QQ邮箱）
                    if "qq.com" in self.smtp_host.lower():
                        logger.warning(f"SMTP_USER应该是完整的邮箱地址，当前值: {login_user}")
                
                if self.smtp_use_tls:
                    # 使用TLS（端口587）
                    server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=timeout)
                    server.set_debuglevel(0)  # 设置为1可以看到详细的SMTP交互信息
                    # 先发送EHLO，再starttls
                    server.ehlo()
                    server.starttls()
                    server.ehlo()  # starttls后需要再次ehlo
                else:
                    # 使用SSL（端口465）
                    server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=timeout)
                    server.set_debuglevel(0)
                
                # 登录（使用完整的邮箱地址）
                server.login(login_user, self.smtp_password)
                server.send_message(msg)
                logger.info(f"邮件发送成功: {to_email}")
                return True
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP认证失败: {to_email}, 错误: {str(e)}")
                raise
            except smtplib.SMTPServerDisconnected as e:
                logger.error(f"SMTP连接断开: {to_email}, 错误: {str(e)}")
                # QQ邮箱可能需要使用SSL而不是TLS
                if self.smtp_use_tls:
                    logger.warning(f"尝试使用SSL连接: {to_email}")
                    try:
                        # 确保使用完整的邮箱地址
                        login_user = self.smtp_user
                        if "@" not in login_user and "@" in self.from_email:
                            login_user = self.from_email
                        
                        server = smtplib.SMTP_SSL(self.smtp_host, 465, timeout=timeout)
                        server.login(login_user, self.smtp_password)
                        server.send_message(msg)
                        logger.info(f"邮件发送成功（使用SSL）: {to_email}")
                        return True
                    except Exception as e2:
                        logger.error(f"SSL连接也失败: {to_email}, 错误: {str(e2)}")
                        raise
                raise
            except Exception as e:
                logger.error(f"邮件发送失败: {to_email}, 错误: {str(e)}")
                raise
            finally:
                if server:
                    try:
                        server.quit()
                    except Exception:
                        pass
            
            logger.info(f"邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {to_email}, 错误: {str(e)}", exc_info=True)
            return False


# 全局邮件服务实例（延迟初始化）
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """获取邮件服务实例（单例模式）"""
    global _email_service
    
    if _email_service is None:
        from ..core.config import settings
        
        _email_service = EmailService(
            smtp_host=getattr(settings, 'smtp_host', ''),
            smtp_port=getattr(settings, 'smtp_port', 587),
            smtp_user=getattr(settings, 'smtp_user', ''),
            smtp_password=getattr(settings, 'smtp_password', ''),
            smtp_use_tls=getattr(settings, 'smtp_use_tls', True),
            from_email=getattr(settings, 'smtp_from_email', ''),
            from_name=getattr(settings, 'smtp_from_name', 'AxiomFlow'),
        )
    
    return _email_service

