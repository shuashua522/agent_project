import uuid

# from agent_project.agentcore.commons.utils import get_llm
#
# llm=get_llm()
# response=llm.invoke("用中文介绍你自己")
# print(response)

from openai import OpenAI

# 配置客户端，指向本地Ollama服务
client = OpenAI(
    base_url="http://localhost:11434/v1",  # Ollama的OpenAI兼容端点
    api_key="ollama"  # 本地调用无需真实API密钥，任意字符串即可
)

# 调用Gemma3（模型名称需与下载的标签一致，如gemma3:4b）
response = client.chat.completions.create(
    model="gemma3:270m",  # 模型标签（与pull/run时一致）
    messages=[
        {"role": "user", "content": "介绍一下你自己"}
    ]
)

# 输出结果
print(response.choices[0].message.content)