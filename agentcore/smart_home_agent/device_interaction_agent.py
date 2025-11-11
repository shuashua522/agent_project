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
from agent_project.agentcore.config.global_config import HOMEASSITANT_AUTHORIZATION_TOKEN, HOMEASSITANT_SERVER, \
    ACTIVE_PROJECT_ENV, PRIVACYHANDLER
from agent_project.agentcore.smart_home_agent.fake_request.fake_do_service import \
    fake_execute_domain_service_by_entity_id, bad_request
from agent_project.agentcore.smart_home_agent.fake_request.fake_get_entity import fake_get_all_entities, \
    fake_get_services_by_domain, fake_get_states_by_entity_id
from agent_project.agentcore.smart_home_agent.privacy_handler import RequestBodyDecodeAgent, replace_encoded_text, \
    jsonBodyDecodeAndCalc

"""
    langgraph关于工具调用的官方文档：
    https://python.langchain.ac.cn/docs/how_to/custom_tools/#tool-decorator
    https://langgraph.com.cn/how-tos/tool-calling.1.html#attach-tools-to-a-model
    
    openai关于工具调用的说明：
    https://platform.openai.com/docs/guides/function-calling/example-use-cases
    
    homeassitant的api调用文档：
    https://developers.home-assistant.io/docs/api/rest/?_highlight=api
"""


token=HOMEASSITANT_AUTHORIZATION_TOKEN
server=HOMEASSITANT_SERVER
active_project_env=ACTIVE_PROJECT_ENV
privacyHandler=PRIVACYHANDLER

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
    result=None
    if active_project_env=="pro":
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
    elif active_project_env == "dev":
        result=fake_get_all_entities()
    elif active_project_env=="test":
        file_path=os.path.join(mock_data_dir, 'selected_entities.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            # 解析JSON文件并返回Python对象
            result=json.load(f)

    return privacyHandler.encodeEntities(result)
@tool
def get_services_by_domain(domain) -> Union[Dict, List]:
    """
    return all services included in the domain.
    """
    if active_project_env == "pro":
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"http://{server}/api/services"

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
    elif active_project_env == "dev":
        return fake_get_services_by_domain(domain)

@tool
def get_states_by_entity_id(entity_id: Annotated[str, "check the status of {entity_id}"],) -> Union[Dict, List]:
    """
    Returns a state object for specified entity_id.
    Returns 404 if not found.
    """
    # entity_id=privacyHandler.decodeEntityId(entity_id)
    entity_id=replace_encoded_text(entity_id)

    result=None
    if active_project_env == "pro":
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"http://{server}/api/states/{entity_id}"

        # 发送GET请求
        response = requests.get(url, headers=headers)
        # 检查请求是否成功
        response.raise_for_status()
        # 返回JSON响应内容
        result=response.json()
    elif active_project_env == "dev":
        result=fake_get_states_by_entity_id(entity_id)
    elif active_project_env == "test":
        file_path = os.path.join(mock_data_dir, 'selected_entities.json')
        result=extract_entity_by_id(file_path,entity_id)

    return privacyHandler.encodeEntity(result)

@tool
def execute_domain_service_by_entity_id(
        domain: Annotated[
            str, "The prefix of entity_id is the corresponding domain. For example, if an entity_id is switch.cuco_cn_269067598_cp1_on_p_2_1, its domain is switch"],
        service: Annotated[
            str, "Obtain all services under the corresponding domain by calling the tool @get_services_by_domain, and select the service that needs to be executed from them"],
        body: Annotated[str, """'Content-Type': 'application/json'. The request body must contain at least 'entity_id' (the body can contain exactly one entity_id). If the service requires other parameters, please supplement them.
                                     All entity_ids can be obtained by calling the tool @get_all_entity_id, and the required entity_id can be selected from them for operation."""]
    ) :
    """
        Calls a service within a specific domain. Will return when the service has been executed.

        Since the data of smart home has been encrypted (the encrypted data is in the form of: @xxx@), if you need to perform arithmetic operations on certain encrypted data passed into the body.
        You can add arithmetic operations before and after it, for example:
        {"entity_id": "@nB/MRO8IqOyD9Kj8t9A3kw==:5sWFd4t1UNtxvhX2LYYaqOZ6aVIKfXw7LiBwXmE/d38n30HHZColHIGWTZPpQlo6@", "brightness_pct": @n+4XiEGjo3K4qp1+WdooLw==:E034U68+xYq6U47e5i/isA==@*5-4}

        This function has no return value and may return null. As long as there is no error, the execution process can be regarded as problem-free.
        """

    body=jsonBodyDecodeAndCalc(body)
    import agent_project.agentcore.config.global_config as global_config
    logger = global_config.GLOBAL_AGENT_DETAILED_LOGGER
    if logger != None:
        logger.info("\n请求的body:\n"+body)
    result=None
    if active_project_env == "pro":
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"http://{server}/api/services/{domain}/{service}"
        # 设置请求体数据
        # payload = {
        #     "entity_id": entity_id
        # }
        payload = json.loads(body)

        # 发送POST请求
        response = requests.post(
            url=url,
            json=payload,  # 自动将字典转换为JSON并设置正确的Content-Type
            headers=headers
        )
        # 检查请求是否成功
        response.raise_for_status()
        # 返回JSON响应
        result= response.json()
    elif active_project_env == "dev":
        result=fake_execute_domain_service_by_entity_id(domain,service,body)
    if result==bad_request:
        return result
    # return result

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
        # prompt = f"""
        #             根据用户的指定，调用提供的工具来获取设备状态或者操作设备
        #             - 因为部分数据涉及隐私，所以你获取的数据可能已被加密，加密后的格式形如@xxx@，具体例子：@nB/MRO8IqOyD9Kj8t9A3kw==:5sWFd4t1UNtxvhX2LYYaqOZ6aVIKfXw7LiBwXmE/d38n30HHZColHIGWTZPpQlo6@
        #             - 如果你要使用这些加密数据，请保留完整格式
        #             - 值得注意的是工具@execute_domain_service_by_entity_id不支持并行调用，所以工具@execute_domain_service_by_entity_id只能调用等结果返回后再接着调用
        #             """
        prompt =f"""
                    According to the user's specification, call the provided tools to obtain device status or operate devices
                    - Since some data involves privacy, the data you obtain may have been encrypted. The encrypted format is like @xxx@, specific example: @nB/MRO8IqOyD9Kj8t9A3kw==:5sWFd4t1UNtxvhX2LYYaqOZ6aVIKfXw7LiBwXmE/d38n30HHZColHIGWTZPpQlo6@
                    - If you need to use this encrypted data, please retain the complete format
                    - It is worth noting that the tool @execute_domain_service_by_entity_id does not support parallel calls, so the tool @execute_domain_service_by_entity_id can only be called after the result of the previous call is returned
                    """
        system_message = {
            "role": "system",
            "content": prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        return {"messages": [response]}

@tool
def deviceInteractionTool(task: Annotated[str, "Natural language description for interacting with smart home devices"])->str:
    """
    Can obtain device status or operate devices based on task descriptions
    :Example 1:
        task="turn off the socket":
    :Example 2:
        task="get the current light intensity"

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