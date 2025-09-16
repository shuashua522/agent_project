import json
import os
from typing import Annotated, List, Callable
from langchain_core.tools import tool
import requests
from typing import Dict, List, Union  # Union 用于表示"或"关系
from langchain.chat_models import init_chat_model
import configparser
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
import json
from typing import Dict, Optional, List

from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm
from agent_project.agentcore.config.global_config import HOMEASSITANT_AUTHORIZATION_TOKEN, get_context_logger

"""
    langgraph关于工具调用的官方文档：
    https://python.langchain.ac.cn/docs/how_to/custom_tools/#tool-decorator
    https://langgraph.com.cn/how-tos/tool-calling.1.html#attach-tools-to-a-model
    
    openai关于工具调用的说明：
    https://platform.openai.com/docs/guides/function-calling/example-use-cases
    
    homeassitant的api调用文档：
    https://developers.home-assistant.io/docs/api/rest/?_highlight=api
"""

logger = get_context_logger()
token=HOMEASSITANT_AUTHORIZATION_TOKEN

# 模拟数据的文件所在目录
mock_data_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),  # 当前文件所在目录
    'test_mock_data'  # 子目录（无开头斜杠）
)


def extract_entity_by_id(json_file_path: str, target_entity_id: str) -> Optional[Dict]:
    """
    从指定JSON文件中提取目标entity_id对应的字典数据

    参数:
        json_file_path: JSON文件的完整路径（如"D:/homeassistant/entities.json"）
        target_entity_id: 要提取的实体ID（如"sun.sun"、"person.shua"）

    返回:
        若找到目标entity_id，返回对应的字典；若未找到或出现异常，返回None
    """
    # 初始化结果为None，默认未找到目标
    target_entity: Optional[Dict] = None

    # 1. 读取JSON文件内容
    with open(json_file_path, 'r', encoding='utf-8') as f:
        # 2. 解析JSON数据，转换为Python列表（数据结构为List[Dict]）
        entity_list: List[Dict] = json.load(f)

        # 3. 验证解析后的数据是否为列表（防止JSON文件格式错误）
        if not isinstance(entity_list, list):
            print(f"错误：JSON文件内容不是列表格式，实际类型为{type(entity_list).__name__}")
            return None

        # 4. 遍历列表，匹配目标entity_id
        for entity in entity_list:
            # 检查当前字典是否包含"entity_id"键（防止数据不完整）
            if "entity_id" not in entity:
                print(f"警告：跳过无效数据，该字典缺少'entity_id'键：{entity}")
                continue

            # 匹配到目标entity_id，记录结果并退出循环
            if entity["entity_id"] == target_entity_id:
                target_entity = entity
                break
    return target_entity

# TODO 将这几个工具都支持获取模拟数据
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
    file_path=os.path.join(mock_data_dir, 'selected_entities.json')
    with open(file_path, 'r', encoding='utf-8') as f:
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
    file_path = os.path.join(mock_data_dir, 'selected_entities.json')
    return extract_entity_by_id(file_path,entity_id)

    # headers = {
    #     "Authorization": f"Bearer {token}",
    #     "Content-Type": "application/json"
    # }
    #
    # url = f"http://localhost:8123/api/states/{entity_id}"
    #
    # # 发送GET请求
    # response = requests.get(url, headers=headers)
    # # 检查请求是否成功
    # response.raise_for_status()
    # # 返回JSON响应内容
    # return response.json()
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

class DeviceInteractionAgent(BaseToolAgent):
    def get_tools(self) -> List[Callable]:
        tools=[get_all_entity_id,
               get_services_by_domain,
               get_states_by_entity_id,
               execute_domain_service_by_entity_id]
        return tools

    def call_tools(self, state: MessagesState):
        llm = get_llm().bind_tools(self.get_tools())
        prompt = f"""
                    根据用户的指定，调用提供的工具来获取设备状态或者操作设备
                    """
        system_message = {
            "role": "system",
            "content": prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        return {"messages": [response]}

@tool
def deviceInteractionTool(task: Annotated[str, "与智能家居设备交互的自然语言描述"])->str:
    """
        能够根据任务描述，获取设备状态或者操作设备
        :示例1:
            task="关闭插座":
        :示例2:
            task="获取当前光照强度"

    """
    return DeviceInteractionAgent().run_agent(task)
# func("门窗关了没")
# func("现在光照如何？")
# func("门窗传感器剩余电量是否充足")
# func("关闭插座")
# func("切换插座状态")
# func("当前光照充足时，切换插座状态")

if __name__ == "__main__":
    # DeviceInteractionAgent().run_agent("网关现在的网络状况如何？")


    # print(mock_data_dir)
    # file_path = os.path.join(mock_data_dir, 'selected_entities.json')
    # with open(file_path, 'r', encoding='utf-8') as f:
    #     # 解析JSON文件并返回Python对象
    #     print(json.load(f))
    pass