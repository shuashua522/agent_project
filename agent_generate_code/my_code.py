from datetime import datetime, timedelta, timezone

# 中国广东属于东八区（UTC+8）
guangdong_tz = timezone(timedelta(hours=8))
now_guangdong = datetime.now(guangdong_tz)
print(now_guangdong.strftime('%Y-%m-%d %H:%M:%S'))