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
        </head>
        <body style="margin: 0; padding: 0; background-color: #f0f9ff; font-family: 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', Arial, sans-serif;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f0f9ff; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; max-width: 600px;">
                            <!-- Header -->
                            <tr>
                                <td style="background-color: #6366f1; padding: 40px 32px; text-align: center;">
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td align="center" style="padding-bottom: 8px;">
                                                <div style="font-size: 32px; font-weight: bold; color: #ffffff; letter-spacing: -0.02em;">AxiomFlow</div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="center">
                                                <div style="font-size: 16px; color: #ffffff; font-weight: 500;">安全验证码</div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <!-- Content -->
                            <tr>
                                <td style="padding: 48px 40px; background-color: #ffffff;">
                                    <div style="font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 16px;">您好！</div>
                                    <div style="font-size: 15px; color: #64748b; line-height: 1.8; margin-bottom: 32px;">
                                        我们收到了您的密码重置请求。为了确保账户安全，请使用以下验证码完成身份验证。
                                    </div>
                                    
                                    <!-- Code Container -->
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f8fafc; border: 2px solid #e0e7ff; border-radius: 12px; margin: 32px 0;">
                                        <tr>
                                            <td style="padding: 32px 24px; text-align: center;">
                                                <div style="font-size: 13px; color: #8b5cf6; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 16px;">验证码</div>
                                                <div style="font-size: 42px; font-weight: bold; letter-spacing: 0.3em; font-family: 'Courier New', monospace; color: #6366f1; margin: 8px 0;">{code}</div>
                                                <div style="font-size: 12px; color: #94a3b8; margin-top: 12px; font-weight: 500;">包含字母和数字，不区分大小写</div>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Warning Box -->
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #fef3c7; border: 1px solid #fbbf24; border-radius: 12px; margin: 32px 0;">
                                        <tr>
                                            <td style="padding: 20px 24px;">
                                                <div style="font-size: 14px; font-weight: 700; color: #d97706; margin-bottom: 8px;">⚠️ 安全提示</div>
                                                <div style="font-size: 14px; color: #92400e; line-height: 1.7;">
                                                    • 验证码有效期为 <strong>5分钟</strong>，请及时使用<br>
                                                    • 请勿将验证码泄露给他人，包括客服人员<br>
                                                    • 如非本人操作，请立即修改密码并联系客服
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Info Section -->
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 40px; padding-top: 32px; border-top: 1px solid #e2e8f0;">
                                        <tr>
                                            <td>
                                                <div style="font-size: 15px; font-weight: 600; color: #334155; margin-bottom: 16px;">💡 使用说明</div>
                                                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                                                    <tr>
                                                        <td style="padding-bottom: 12px; font-size: 14px; color: #64748b; line-height: 1.8;">
                                                            <span style="color: #10b981; font-weight: bold; margin-right: 8px;">✓</span>在密码重置页面输入上述6位验证码（字母+数字）
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding-bottom: 12px; font-size: 14px; color: #64748b; line-height: 1.8;">
                                                            <span style="color: #10b981; font-weight: bold; margin-right: 8px;">✓</span>验证码不区分大小写，可直接输入
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding-bottom: 12px; font-size: 14px; color: #64748b; line-height: 1.8;">
                                                            <span style="color: #10b981; font-weight: bold; margin-right: 8px;">✓</span>验证通过后即可设置新密码
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="font-size: 14px; color: #64748b; line-height: 1.8;">
                                                            <span style="color: #10b981; font-weight: bold; margin-right: 8px;">✓</span>验证码仅可使用一次，使用后立即失效
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <div style="height: 1px; background-color: #e2e8f0; margin: 24px 0;"></div>
                                    
                                    <div style="font-size: 13px; color: #94a3b8; line-height: 1.8; margin-bottom: 0;">
                                        如果您没有请求此验证码，请忽略此邮件。您的账户仍然安全，无需采取任何操作。
                                    </div>
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 32px 40px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center;">
                                    <p style="font-size: 13px; color: #94a3b8; margin: 0; line-height: 1.7;">此邮件由 AxiomFlow 系统自动发送，请勿回复。</p>
                                    <p style="font-size: 12px; color: #cbd5e1; margin: 16px 0 0 0; font-weight: 500;">© 2024 AxiomFlow Team. All rights reserved.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
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
    
    def send_email_verification(self, to_email: str, verification_url: str, user_name: str = "") -> bool:
        """
        发送邮箱验证邮件
        
        Args:
            to_email: 收件人邮箱
            verification_url: 验证链接URL
            user_name: 用户名称（可选）
            
        Returns:
            是否发送成功
        """
        subject = "AxiomFlow 邮箱验证 | 请验证您的邮箱地址"
        display_name = user_name or to_email.split("@")[0]
        
        text_content = f"""
亲爱的 {display_name}，

欢迎注册 AxiomFlow！

请点击以下链接验证您的邮箱地址：
{verification_url}

此链接将在24小时内有效。

如果您没有注册 AxiomFlow，请忽略此邮件。

祝好，
AxiomFlow 团队
        """
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; background-color: #f0f9ff; font-family: 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', Arial, sans-serif;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f0f9ff; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; max-width: 600px;">
                            <!-- Header -->
                            <tr>
                                <td style="background-color: #6366f1; padding: 40px 32px; text-align: center;">
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td align="center" style="padding-bottom: 8px;">
                                                <div style="font-size: 32px; font-weight: bold; color: #ffffff; letter-spacing: -0.02em;">AxiomFlow</div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="center">
                                                <div style="font-size: 16px; color: #ffffff; font-weight: 500;">邮箱验证</div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <!-- Content -->
                            <tr>
                                <td style="padding: 48px 40px; background-color: #ffffff;">
                                    <div style="font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 16px;">亲爱的 {display_name}，</div>
                                    <div style="font-size: 15px; color: #64748b; line-height: 1.8; margin-bottom: 32px;">
                                        欢迎注册 AxiomFlow！<br>
                                        为了确保账户安全，请验证您的邮箱地址。验证后您将可以正常使用所有功能。
                                    </div>
                                    
                                    <!-- Button -->
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 40px 0;">
                                        <tr>
                                            <td align="center">
                                                <a href="{verification_url}" style="display: inline-block; padding: 16px 40px; background-color: #6366f1; color: #ffffff; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 16px;">验证邮箱地址</a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Link Fallback -->
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f8fafc; border-left: 4px solid #6366f1; border-radius: 8px; margin-top: 24px;">
                                        <tr>
                                            <td style="padding: 20px;">
                                                <div style="font-size: 14px; font-weight: 600; color: #475569; margin-bottom: 8px;">如果按钮无法点击，请复制以下链接到浏览器：</div>
                                                <div style="font-size: 13px; color: #6366f1; word-break: break-all; font-family: monospace;">{verification_url}</div>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Warning -->
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 24px;">
                                        <tr>
                                            <td style="padding: 16px; background-color: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 8px;">
                                                <div style="font-size: 14px; color: #92400e;">⚠️ 此链接将在24小时内有效。如果您没有注册 AxiomFlow，请忽略此邮件。</div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 32px 40px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center;">
                                    <p style="font-size: 13px; color: #64748b; margin: 0; line-height: 1.7;">此邮件由 AxiomFlow 系统自动发送，请勿回复。</p>
                                    <p style="font-size: 13px; color: #64748b; margin: 8px 0 0 0; line-height: 1.7;">© 2024 AxiomFlow. All rights reserved.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return self._send_email(to_email, subject, text_content, html_content)
    
    def send_login_alert(self, to_email: str, user_name: str, ip: str, user_agent: str, login_time: str, location: str = "") -> bool:
        """
        发送异常登录通知邮件
        
        Args:
            to_email: 收件人邮箱
            user_name: 用户名称
            ip: 登录IP地址
            user_agent: 用户代理字符串
            login_time: 登录时间
            location: IP地理位置（可选）
            
        Returns:
            是否发送成功
        """
        subject = "AxiomFlow 安全提醒 | 检测到新设备登录"
        display_name = user_name or to_email.split("@")[0]
        device_info = self._parse_user_agent(user_agent)
        
        text_content = f"""
亲爱的 {display_name}，

我们检测到您的账户在以下位置登录：

登录时间：{login_time}
IP地址：{ip}
设备信息：{device_info}
{f'地理位置：{location}' if location else ''}

如果您确认这是您的操作，可以忽略此邮件。

如果您不认识此次登录，请立即：
1. 修改您的账户密码
2. 检查账户安全设置
3. 撤销所有活跃会话

祝好，
AxiomFlow 安全团队
        """
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; background-color: #fef3c7; font-family: 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', Arial, sans-serif;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #fef3c7; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; max-width: 600px;">
                            <!-- Header -->
                            <tr>
                                <td style="background-color: #f59e0b; padding: 40px 32px; text-align: center;">
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td align="center" style="padding-bottom: 16px;">
                                                <div style="width: 64px; height: 64px; background-color: rgba(255, 255, 255, 0.2); border-radius: 50%; margin: 0 auto; display: inline-block; line-height: 64px; text-align: center; font-size: 36px; color: #ffffff;">⚠️</div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="center" style="padding-bottom: 8px;">
                                                <div style="font-size: 28px; font-weight: bold; color: #ffffff; letter-spacing: -0.02em;">AxiomFlow</div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="center">
                                                <div style="font-size: 16px; color: #ffffff; font-weight: 500;">安全提醒</div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <!-- Content -->
                            <tr>
                                <td style="padding: 48px 40px; background-color: #ffffff;">
                                    <div style="font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 24px;">亲爱的 {display_name}，</div>
                                    
                                    <!-- Alert Box -->
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 8px; margin-bottom: 32px;">
                                        <tr>
                                            <td style="padding: 20px;">
                                                <div style="font-size: 16px; font-weight: 600; color: #92400e; margin-bottom: 12px;">⚠️ 检测到新设备登录</div>
                                                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                                                    <tr>
                                                        <td style="padding-bottom: 12px;">
                                                            <span style="font-weight: 600; color: #78350f; display: inline-block; width: 80px;">登录时间：</span>
                                                            <span style="color: #92400e;">{login_time}</span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding-bottom: 12px;">
                                                            <span style="font-weight: 600; color: #78350f; display: inline-block; width: 80px;">IP地址：</span>
                                                            <span style="color: #92400e;">{ip}</span>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding-bottom: 12px;">
                                                            <span style="font-weight: 600; color: #78350f; display: inline-block; width: 80px;">设备信息：</span>
                                                            <span style="color: #92400e;">{device_info}</span>
                                                        </td>
                                                    </tr>
                                                    {f'<tr><td><span style="font-weight: 600; color: #78350f; display: inline-block; width: 80px;">地理位置：</span><span style="color: #92400e;">{location}</span></td></tr>' if location else ''}
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="color: #64748b; margin-bottom: 24px; line-height: 1.7;">
                                        如果您确认这是您的操作，可以忽略此邮件。
                                    </p>
                                    
                                    <!-- Warning Box -->
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #fee2e2; border-left: 4px solid #ef4444; border-radius: 8px; margin-top: 32px;">
                                        <tr>
                                            <td style="padding: 20px;">
                                                <div style="font-size: 16px; font-weight: 600; color: #991b1b; margin-bottom: 12px;">如果您不认识此次登录，请立即：</div>
                                                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                                                    <tr>
                                                        <td style="padding-bottom: 8px; color: #7f1d1d;">
                                                            <span style="color: #ef4444; font-weight: bold; margin-right: 8px;">•</span>修改您的账户密码
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding-bottom: 8px; color: #7f1d1d;">
                                                            <span style="color: #ef4444; font-weight: bold; margin-right: 8px;">•</span>检查账户安全设置
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="color: #7f1d1d;">
                                                            <span style="color: #ef4444; font-weight: bold; margin-right: 8px;">•</span>撤销所有活跃会话
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 32px 40px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center;">
                                    <p style="font-size: 13px; color: #64748b; margin: 0; line-height: 1.7;">此邮件由 AxiomFlow 系统自动发送，请勿回复。</p>
                                    <p style="font-size: 13px; color: #64748b; margin: 8px 0 0 0; line-height: 1.7;">© 2024 AxiomFlow. All rights reserved.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return self._send_email(to_email, subject, text_content, html_content)
    
    def _parse_user_agent(self, user_agent: str) -> str:
        """解析User-Agent，返回简化的设备信息"""
        if not user_agent:
            return "未知设备"
        ua_lower = user_agent.lower()
        if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
            if "android" in ua_lower:
                return "Android 设备"
            if "iphone" in ua_lower or "ipad" in ua_lower:
                return "iOS 设备"
            return "移动设备"
        if "chrome" in ua_lower and "edg" not in ua_lower:
            return "Chrome 浏览器"
        if "firefox" in ua_lower:
            return "Firefox 浏览器"
        if "safari" in ua_lower and "chrome" not in ua_lower:
            return "Safari 浏览器"
        if "edg" in ua_lower:
            return "Edge 浏览器"
        return "未知设备"
    
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

