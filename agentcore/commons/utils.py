import configparser
import logging
import re

from langchain.chat_models import init_chat_model

from agent_project.agentcore.config.global_config import MODEL, BASE_URL, API_KEY, PROXIES, PROVIDER


def get_llm():

    provider=PROVIDER
    model = MODEL
    base_url = BASE_URL
    api_key = API_KEY

    llm = None
    if (provider == "openai"):
        proxies = PROXIES
        import httpx
        httpx_client = httpx.Client()
        httpx_client.proxies = proxies

        llm = init_chat_model(
            model=model,
            model_provider="openai",
            api_key=api_key,
            base_url=base_url,
            temperature=0,
            http_client=httpx_client
        )
    else:
        llm = init_chat_model(
            model=model,
            model_provider="openai",
            api_key=api_key,
            base_url=base_url,
            temperature=0,
        )
    return llm

def remove_thinks(text):
    # 匹配 <think> 和 </think> 之间的所有内容（包括标签）
    # .*? 表示非贪婪匹配，确保只匹配到最近的 </think>
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

def get_null_logger():
    null_logger = logging.getLogger("null_logger")
    null_logger.addHandler(logging.NullHandler())  # 添加空处理器
    null_logger.setLevel(logging.CRITICAL + 1)  # 级别设置为最高，屏蔽所有日志
    return null_logger

if __name__ == "__main__":
    # print(get_llm().invoke("1+1=？"))
    pass