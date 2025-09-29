from langchain.chat_models import ChatOpenAI

from bin.config import set_environment_variables
from sage.utils.llm_utils import GPTConfig

# 导入必要的消息类
from langchain.schema import SystemMessage, HumanMessage

# model_name: str = "ep-20250805172515-6d5kv"
# openai_api_base: str = "https://ark.cn-beijing.volces.com/api/v3/"
# openai_api_key: str = "5950638e-f4c0-45d0-a005-cd9331ecada8"
# ========
# api_key = "sk-70bd7714a49d4808af6a939853fcbfce"
# base_url= "https://api.deepseek.com/v1"
# model= "deepseek-reasoner"
# ===============
api_key = "5950638e-f4c0-45d0-a005-cd9331ecada8"
base_url = "https://ark.cn-beijing.volces.com/api/v3"
model = "ep-20250805172515-6d5kv"
# 初始化模型（你的原有代码）
# chat_llm = GPTConfig().instantiate()
chat_llm = ChatOpenAI(
    model_name=model,  # 如 "llama-2-7b-chat"
    openai_api_base=base_url,  # 本地 API 地址
    openai_api_key=api_key  # 本地模型通常不需要密钥，填任意值
)
# 构造对话消息（使用 LangChain 的消息对象，而非字典）
messages = [
    SystemMessage(content="你是一个 helpful 的助手。"),  # 系统提示（对应 role="system"）
    HumanMessage(content="什么是人工智能？")             # 用户提问（对应 role="user"）
]

# 调用模型
response = chat_llm.invoke(messages)

# 提取回答内容
print("回答：", response.content)

