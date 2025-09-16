import random
import os
import threading

from langchain.chat_models import init_chat_model
import configparser
import logging
import time

from agent_project.utils.qq_email_sender import send_email_to_self

def get_llm(provider):
    # 创建配置解析器对象
    config = configparser.ConfigParser()
    # 读取INI文件
    config.read('my_config.ini', encoding='utf-8')
    # 设置LangSmith跟踪开关和API密钥
    os.environ["LANGSMITH_TRACING"] = config.get('LangSmith', 'langsmith_tracing')
    os.environ["LANGSMITH_API_KEY"] = config.get('LangSmith', 'langsmith_api_key')

    # provider = "doubao"
    model = config.get(provider, 'model')
    base_url = config.get(provider, 'base_url')
    api_key = config.get(provider, 'api_key')

    llm = None
    if (provider == "openai"):
        proxies = {
            'http': 'http://127.0.0.1:33210',  # HTTP 请求使用 33210 端口的 HTTP 代理
            'https': 'http://127.0.0.1:33210',  # HTTPS 请求使用 33210 端口的 HTTP 代理
        }
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

llm=get_llm("openai")

user_message = {
    "role": "user",
    "content": "5+6=?",
}

response = llm.invoke([user_message])
print(response)