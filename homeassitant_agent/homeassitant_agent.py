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

token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkNzgwYTkyZGI2OTE0ZWExYTg2OGE1NmQ5ODcwOTU0OCIsImlhdCI6MTc1NjExODAwMywiZXhwIjoyMDcxNDc4MDAzfQ.DD600u9b5nGB0AwzVoIhonY2ACOs43Vp3IVvL5XN5aw"

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
@tool
def get_all_entity_id()-> Union[Dict, List]:
    """
    Returns an array of state objects.
    Each state has the following attributes: entity_id, state, last_changed and attributes.
    """
    # headers = {
    #     "Authorization": f"Bearer {token}",
    #     "Content-Type": "application/json"
    # }
    #
    # url = "http://localhost:8123/api/states"
    #
    # # 发送GET请求
    # response = requests.get(url, headers=headers)
    # # 检查请求是否成功
    # response.raise_for_status()
    # # 返回JSON响应内容
    # return response.json()
    with open("selected_entities.json", 'r', encoding='utf-8') as f:
        # 解析JSON文件并返回Python对象
        return json.load(f)
@tool
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

@tool
def get_states_by_entity_id(entity_id: Annotated[str, "查看{entity_id}的状态"],) -> Union[Dict, List]:
    """
    Returns a state object for specified entity_id.
    Returns 404 if not found.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"http://localhost:8123/api/states/{entity_id}"

    # 发送GET请求
    response = requests.get(url, headers=headers)
    # 检查请求是否成功
    response.raise_for_status()
    # 返回JSON响应内容
    return response.json()
@tool
def execute_domain_service_by_entity_id(
        domain: Annotated[str, "entity_id的前缀即为对应的domain，比如某一entity_id为switch.cuco_cn_269067598_cp1_on_p_2_1，其domain即为switch"],
        service: Annotated[str, "通过调用工具@get_services_by_domain获取对应domain下的所有的services，从中选择需要执行的服务"],
        entity_id: Annotated[str, "通过调用工具@get_all_entity_id可以获取所有的entity_id，从中选择所需的entity_id进行操作。"],
    ) -> Union[Dict, List]:
    """
    Calls a service within a specific domain. Will return when the service has been executed.
    You can pass an optional JSON object to be used as service_data.
    {
        "entity_id": "light.Ceiling"
    }

    Returns a list of states that have changed while the service was being executed, and optionally response data, if supported by the service.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"http://localhost:8123/api/services/{domain}/{service}"
    # 设置请求体数据
    payload = {
        "entity_id": entity_id
    }

    # 发送POST请求
    response = requests.post(
        url=url,
        json=payload,  # 自动将字典转换为JSON并设置正确的Content-Type
        headers=headers
    )
    # 检查请求是否成功
    response.raise_for_status()
    # 返回JSON响应
    return response.json()

def tools_test():
    # 正确调用无参数工具
    print(get_all_entity_id.invoke({}))  # 无参数时传入空字典

    # 正确调用其他工具
    # print(get_services_by_domain.invoke({}))

    print(get_states_by_entity_id.invoke({
        "entity_id": "binary_sensor.isa_cn_blt_3_1md0u6qht0k00_dw2hl_contact_state_p_2_2"
    }))

    print(execute_domain_service_by_entity_id.invoke({
        "domain": "switch",
        "service": "toggle",
        "entity_id": "switch.cuco_cn_269067598_cp1_on_p_2_1"
    }))

tools=[get_all_entity_id,get_services_by_domain,get_states_by_entity_id,execute_domain_service_by_entity_id]

llm=get_llm("doubao")
llm_with_tools = llm.bind_tools(tools)
# print(llm_with_tools.invoke("一共有哪些entity_id？"))

tool_node = ToolNode(tools)

def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

def call_model(state: MessagesState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

builder = StateGraph(MessagesState)

# Define the two nodes we will cycle between
builder.add_node("call_model", call_model)
builder.add_node("tools", tool_node)

builder.add_edge(START, "call_model")
builder.add_conditional_edges("call_model", should_continue, ["tools", END])
builder.add_edge("tools", "call_model")

agent = builder.compile()

# problem="关闭插座"
# agent.invoke({"messages": [{"role": "user", "content": problem}]})

def func(problem):
    last_message = None  # 初始化最后一个消息变量

    for step in agent.stream(
            {"messages": [{"role": "user", "content": problem}]},
            stream_mode="values",
    ):
        last_message = step["messages"][-1]  # 更新最后一个消息
        # 如果你不需要打印中间步骤，可以移除下面这行
        last_message.pretty_print()

    # return remove_code_run_prefix(last_message.content)  # 返回最后一个消息

func("门窗传感器剩余电量是否充足")
