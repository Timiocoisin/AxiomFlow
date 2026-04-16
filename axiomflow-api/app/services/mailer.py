from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Optional, Tuple

from app.core.config import get_settings


logger = logging.getLogger("axiomflow.mailer")


def _parse_from(from_value: str) -> Tuple[Optional[str], str]:
    # Very small parser: "Name <email>" or "email"
    v = from_value.strip()
    if "<" in v and ">" in v:
        name = v.split("<", 1)[0].strip().strip('"')
        email = v.split("<", 1)[1].split(">", 1)[0].strip()
        return (name or None, email)
    return (None, v)


def send_email(*, to_email: str, subject: str, text: str, html: Optional[str] = None) -> None:
    settings = get_settings()
    from_name, from_email = _parse_from(settings.SMTP_FROM_EMAIL)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["To"] = to_email
    msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")

    try:
        # QQ/163 commonly use implicit SSL on 465.
        if int(settings.SMTP_PORT) == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
                smtp.ehlo()
                if settings.SMTP_USERNAME:
                    smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                smtp.send_message(msg)
            return

        # Other ports (e.g. 587) use SMTP + optional STARTTLS.
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            smtp.ehlo()
            if settings.SMTP_USE_TLS:
                smtp.starttls()
                smtp.ehlo()
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
    except Exception:
        logger.exception("smtp_send_failed")
        raise


def send_verification_email(*, to_email: str, token: str) -> None:
    settings = get_settings()
    link = f"{settings.PUBLIC_WEB_URL}/#/verify-email?token={token}"
    subject = "Axiomflow 邮箱验证"
    text = (
        "Axiomflow 邮箱验证\n\n"
        "请点击下方链接完成邮箱验证：\n"
        f"{link}\n\n"
        "该链接将在 60 分钟后过期。\n"
        "如果这不是你的操作，请忽略这封邮件。"
    )
    html = f"""\
<!doctype html>
<html lang="zh-CN">
  <body style="margin:0;padding:0;background:#f3f6fb;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f3f6fb;padding:28px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="640" style="width:640px;max-width:640px;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #e9eef7;">
            <tr>
              <td style="padding:28px 32px 18px;background:linear-gradient(120deg,#4f46e5,#7c3aed);">
                <div style="font-size:12px;letter-spacing:.08em;color:#e0e7ff;font-weight:700;">AXIOMFLOW</div>
                <div style="margin-top:8px;font-size:24px;line-height:1.3;color:#ffffff;font-weight:700;">邮箱验证</div>
                <div style="margin-top:8px;font-size:14px;line-height:1.6;color:#e0e7ff;">确认你的邮箱后即可完整使用账号功能。</div>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 32px 8px;font-family:Arial,'PingFang SC','Microsoft YaHei',sans-serif;color:#0f172a;">
                <p style="margin:0 0 16px;font-size:15px;line-height:1.8;color:#334155;">你好，</p>
                <p style="margin:0 0 18px;font-size:15px;line-height:1.8;color:#334155;">
                  请点击下方按钮完成邮箱验证。
                </p>
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 20px;">
                  <tr>
                    <td align="center" bgcolor="#4f46e5" style="border-radius:10px;">
                      <a href="{link}" style="display:inline-block;padding:12px 22px;color:#ffffff;text-decoration:none;font-size:14px;font-weight:700;">
                        验证邮箱
                      </a>
                    </td>
                  </tr>
                </table>
                <p style="margin:0 0 10px;font-size:13px;color:#64748b;">若按钮不可点击，请复制以下链接到浏览器打开：</p>
                <p style="margin:0 0 8px;word-break:break-all;">
                  <a href="{link}" style="color:#4f46e5;font-size:13px;line-height:1.7;text-decoration:none;">{link}</a>
                </p>
                <p style="margin:0 0 14px;font-size:13px;color:#94a3b8;">该链接有效期为 60 分钟。</p>
              </td>
            </tr>
            <tr>
              <td style="padding:16px 32px 26px;border-top:1px solid #eef2f7;font-family:Arial,'PingFang SC','Microsoft YaHei',sans-serif;">
                <p style="margin:0;font-size:12px;line-height:1.8;color:#94a3b8;">
                  若非本人操作，请忽略此邮件。<br/>
                  此邮件由系统自动发送，请勿直接回复。<br/>
                  联系邮箱：support@axiomflow.com
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
    send_email(to_email=to_email, subject=subject, text=text, html=html)


def send_password_reset_email(*, to_email: str, token: str) -> None:
    settings = get_settings()
    link = f"{settings.PUBLIC_WEB_URL}/#/reset-password?token={token}"
    subject = "Axiomflow 重置密码"
    text = (
        "Axiomflow 重置密码\n\n"
        "请点击下方链接继续重置密码：\n"
        f"{link}\n\n"
        "该链接将在 30 分钟后过期。\n"
        "如果这不是你的操作，请忽略这封邮件。"
    )
    html = f"""\
<!doctype html>
<html lang="zh-CN">
  <body style="margin:0;padding:0;background:#f3f6fb;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f3f6fb;padding:28px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="640" style="width:640px;max-width:640px;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #e9eef7;">
            <tr>
              <td style="padding:28px 32px 18px;background:linear-gradient(120deg,#0f172a,#334155);">
                <div style="font-size:12px;letter-spacing:.08em;color:#cbd5e1;font-weight:700;">AXIOMFLOW</div>
                <div style="margin-top:8px;font-size:24px;line-height:1.3;color:#ffffff;font-weight:700;">重置密码</div>
                <div style="margin-top:8px;font-size:14px;line-height:1.6;color:#cbd5e1;">请在链接有效期内完成密码重置操作。</div>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 32px 8px;font-family:Arial,'PingFang SC','Microsoft YaHei',sans-serif;color:#0f172a;">
                <p style="margin:0 0 16px;font-size:15px;line-height:1.8;color:#334155;">你好，</p>
                <p style="margin:0 0 18px;font-size:15px;line-height:1.8;color:#334155;">
                  系统收到了重置密码请求，请点击下方按钮继续。
                </p>
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 20px;">
                  <tr>
                    <td align="center" bgcolor="#0f172a" style="border-radius:10px;">
                      <a href="{link}" style="display:inline-block;padding:12px 22px;color:#ffffff;text-decoration:none;font-size:14px;font-weight:700;">
                        重置密码
                      </a>
                    </td>
                  </tr>
                </table>
                <p style="margin:0 0 10px;font-size:13px;color:#64748b;">若按钮不可点击，请复制以下链接到浏览器打开：</p>
                <p style="margin:0 0 8px;word-break:break-all;">
                  <a href="{link}" style="color:#0f172a;font-size:13px;line-height:1.7;text-decoration:none;">{link}</a>
                </p>
                <p style="margin:0 0 14px;font-size:13px;color:#94a3b8;">该链接有效期为 30 分钟。</p>
              </td>
            </tr>
            <tr>
              <td style="padding:16px 32px 26px;border-top:1px solid #eef2f7;font-family:Arial,'PingFang SC','Microsoft YaHei',sans-serif;">
                <p style="margin:0;font-size:12px;line-height:1.8;color:#94a3b8;">
                  若非本人操作，请忽略此邮件。<br/>
                  此邮件由系统自动发送，请勿直接回复。<br/>
                  联系邮箱：support@axiomflow.com
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
    send_email(to_email=to_email, subject=subject, text=text, html=html)

