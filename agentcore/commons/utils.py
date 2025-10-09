import configparser
import logging
import os
import re
from pathlib import Path

from langchain.chat_models import init_chat_model

from agent_project.agentcore.config.global_config import MODEL, BASE_URL, API_KEY, PROXIES, PROVIDER

# 获取当前文件的绝对路径
current_file_path = os.path.abspath(__file__)
# 定位所在目录
current_dir = os.path.dirname(current_file_path)

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

def get_context_logger(log_file=None, name=__name__):
    """配置能自动打印模块、类、函数信息的日志器"""
    # 处理默认日志文件路径
    if log_file is None:
        # 这里使用最新的 config_dir 值
        log_file = os.path.join(current_dir, 'agent_call.log')
    # 确保日志目录存在
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 格式化字符串：包含模块、函数、行号等信息
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s'
    )

    # 创建处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    # console_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    # console_handler.setFormatter(formatter)

    # 配置日志器
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    # logger.addHandler(console_handler)

    return logger

if __name__ == "__main__":
    # print(get_llm().invoke("1+1=？"))
    pass