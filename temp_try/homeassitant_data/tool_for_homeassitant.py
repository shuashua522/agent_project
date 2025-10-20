import requests

from agent_project.agentcore.config.global_config import HOMEASSITANT_AUTHORIZATION_TOKEN, HOMEASSITANT_SERVER

token=HOMEASSITANT_AUTHORIZATION_TOKEN
server=HOMEASSITANT_SERVER

headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

url = f"http://{server}/api/states"

# 发送GET请求
response = requests.get(url, headers=headers)
# 检查请求是否成功
response.raise_for_status()
# 返回JSON响应内容
result=response.json()
print(result)