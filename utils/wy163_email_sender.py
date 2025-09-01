import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart


def send_email_via_163(sender_email, auth_code, receiver_email, subject, content, is_html=False):
    """
    通过163邮箱发送邮件（修复From字段格式问题）
    """
    # 1. 配置SMTP服务器
    smtp_server = "smtp.163.com"
    smtp_port = 465  # 加密端口

    # 2. 创建邮件对象
    msg = MIMEMultipart()

    # 关键修复：From字段必须严格为发件人邮箱，避免添加额外标识导致格式错误
    # 格式必须符合 RFC 标准："邮箱地址" 或 "显示名 <邮箱地址>"
    msg['From'] = sender_email  # 直接使用发件人邮箱作为From字段
    # 如需显示名称，正确格式应为：
    # msg['From'] = f"{Header('发送者名称', 'utf-8')} <{sender_email}>"

    msg['To'] = receiver_email
    msg['Subject'] = Header(subject, 'utf-8')  # 主题保持不变

    # 3. 添加邮件内容
    content_type = 'html' if is_html else 'plain'
    msg.attach(MIMEText(content, content_type, 'utf-8'))

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, auth_code)
            server.sendmail(
                sender_email,
                receiver_email.split(','),
                msg.as_string()
            )

        print("邮件发送成功！")
        return True

    except smtplib.SMTPException as e:
        print(f"邮件发送失败: {str(e)}")
        return False

def send_email_to_self(subject,content="内容空空如也"):
    # 替换为实际信息
    SENDER_EMAIL = "shuashua_world@163.com"  # 你的163邮箱
    AUTH_CODE = "SYXDdK73j8sV5DuN"  # 163邮箱授权码
    RECEIVER_EMAIL = "2496091908@qq.com"  # 收件人邮箱

    send_email_via_163(
        sender_email=SENDER_EMAIL,
        auth_code=AUTH_CODE,
        receiver_email=RECEIVER_EMAIL,
        subject=subject,
        content=content
    )
# 使用示例
if __name__ == "__main__":
    # 替换为实际信息
    SENDER_EMAIL = "shuashua_world@163.com"  # 你的163邮箱
    AUTH_CODE = "SYXDdK73j8sV5DuN"  # 163邮箱授权码
    RECEIVER_EMAIL = "2496091908@qq.com"  # 收件人邮箱
    SUBJECT = "测试163邮箱发送邮件"
    CONTENT = "这是一封修复From字段后的测试邮件！"

    send_email_via_163(
        sender_email=SENDER_EMAIL,
        auth_code=AUTH_CODE,
        receiver_email=RECEIVER_EMAIL,
        subject=SUBJECT,
        content=CONTENT
    )
