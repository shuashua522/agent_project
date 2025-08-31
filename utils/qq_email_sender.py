import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr


def send_email(sender_email, auth_code, subject, content):
    """
    使用QQ邮箱发送邮件给自己，修复了From头部格式问题

    参数:
        sender_email: QQ邮箱地址（如：123456@qq.com）
        auth_code: QQ邮箱SMTP授权码（不是登录密码）
        subject: 邮件主题
        content: 邮件内容
    """
    # 邮件服务器设置
    smtp_server = 'smtp.qq.com'
    smtp_port = 587  # QQ邮箱SMTP端口（TLS加密）

    # 创建邮件内容
    message = MIMEText(content, 'plain', 'utf-8')

    # 修复From头部格式，使用formataddr确保符合RFC标准
    sender_name = "自己"
    message['From'] = formataddr((Header(sender_name, 'utf-8').encode(), sender_email))
    message['To'] = formataddr((Header(sender_name, 'utf-8').encode(), sender_email))
    message['Subject'] = Header(subject, 'utf-8')

    try:
        # 连接邮件服务器并发送邮件
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # 启用TLS加密
        server.login(sender_email, auth_code)  # 登录邮箱

        # 发送邮件
        server.sendmail(sender_email, [sender_email], message.as_string())
        print("邮件发送成功！")

        # 正确关闭连接
        server.quit()
        return True

    except smtplib.SMTPException as e:
        print(f"邮件发送失败：{str(e)}")
        return False

def send_email_to_self(subject,content="内容空空如也"):
    # 配置信息（请替换为你自己的信息）
    qq_email = "2496091908@qq.com"  # 你的QQ邮箱地址
    authorization_code = "vffcrvirqjrrebfg"  # 你的QQ邮箱SMTP授权码

    # 发送测试邮件
    send_email(
        sender_email=qq_email,
        auth_code=authorization_code,
        subject=subject,
        content=content
    )


# 使用示例
if __name__ == "__main__":
    send_email_to_self("代码运行完毕")