import json
import os
from typing import Annotated, List
from langchain_core.tools import tool
import requests
from typing import Dict, List, Union  # Union 用于表示"或"关系
from langchain.chat_models import init_chat_model
import configparser
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END

"""
    langgraph关于工具调用的官方文档：
    https://python.langchain.ac.cn/docs/how_to/custom_tools/#tool-decorator
    https://langgraph.com.cn/how-tos/tool-calling.1.html#attach-tools-to-a-model

    openai关于工具调用的说明：
    https://platform.openai.com/docs/guides/function-calling/example-use-cases

    homeassitant的api调用文档：
    https://developers.home-assistant.io/docs/api/rest/?_highlight=api
"""

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkNzgwYTkyZGI2OTE0ZWExYTg2OGE1NmQ5ODcwOTU0OCIsImlhdCI6MTc1NjExODAwMywiZXhwIjoyMDcxNDc4MDAzfQ.DD600u9b5nGB0AwzVoIhonY2ACOs43Vp3IVvL5XN5aw"


def get_services_by_domain(domain) -> Union[Dict, List]:
    """
    return all services included in the domain.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = "http://localhost:8123/api/services"

    # 发送GET请求
    response = requests.get(url, headers=headers)
    # 检查请求是否成功
    response.raise_for_status()
    # 返回JSON响应内容
    all_domain_and_services = response.json()
    for domain_entry in all_domain_and_services:
        # 匹配目标 domain
        if domain_entry.get("domain") == domain:
            # 返回该 domain 对应的 services 字典
            return domain_entry
        # 若未找到目标 domain，返回空字典
    return {}


# print(get_services_by_domain("button"))
with open("selected_entities.json", 'r', encoding='utf-8') as f:
    # 解析JSON文件并返回Python对象
    print(type(json.load(f)))