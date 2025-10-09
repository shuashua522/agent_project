"""
An agent for interaction with SmartThings devices.

Used as a tool SAGE.
"""
import json
import os
from dataclasses import dataclass
from dataclasses import field
from difflib import SequenceMatcher
from typing import Any, Dict, Optional
from typing import List
from typing import Type

import numpy as np
import requests
from langchain.agents.agent import AgentExecutor
from langchain.agents.mrkl.base import ZeroShotAgent
from langchain.agents.tools import BaseTool
from langchain.chains.llm import LLMChain
from langchain.chat_models.base import BaseChatModel
from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import HumanMessagePromptTemplate
from langchain.schema.messages import SystemMessage

# import sage.testing.fake_requests
from sage.base import BaseConfig
from sage.base import BaseToolConfig
from sage.base import SAGEBaseTool
from sage.smartthings.device_doc import DEVICE_INFO_DOC
# from sage.smartthings.device_disambiguation import DeviceDisambiguationToolConfig
# from sage.smartthings.docmanager import DocManager
from sage.utils.common import parse_json
from sage.utils.llm_utils import LLMConfig
from sage.utils.llm_utils import TGIConfig
from sage.utils.logging_utils import get_callback_handlers


def most_similar_id(device, all_devices):
    sims = [SequenceMatcher(None, device, d).ratio() for d in all_devices]
    idx = np.argmax(sims)
    closest_sim = sims[idx]

    if closest_sim > 0.5:
        return all_devices[idx]

    return "to use the planner to figure out the right ID"






def create_and_run_smartthings_agent_v2(
    command: str, llm: BaseChatModel, logpath: str, tools: List[BaseTool]
) -> str:
    tool_names = ", ".join([tool.name for tool in tools])
    tool_descriptions = "\n".join(
        [f"{tool.name}: {tool.description}" for tool in tools]
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                # TODO 改掉了不适配的提示词
                # TODO 这里也需要设备ID，还未改
                content=f"""
You are an agent that assists with queries against some API.

Instructions:
- Include a description of what you've done in the final answer, include device IDs
- If you encounter an error, try to think what is the best action to solve the error instead of trial and error.

Here are the tools to plan and execute API requests:
{tool_descriptions}

Starting below, you should follow this format:

User query: the query a User wants help with related to the API
Thought: you should always think about what to do
Action: the action to take, should be one of the tools [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I am finished executing a plan and have the information the user asked for or the data the user asked to create
Final Answer: the final output from executing the plan. Add <FINISHED> after your final answer.

Your must always output a thought, action, and action input.
Do not forget to say I'm finished when the user's command is executed.
Begin!
"""
            ),
            HumanMessagePromptTemplate.from_template(
                """
User query: {input}
Thought: I should generate a plan to help with this query.
{agent_scratchpad}
""",
                input_variables=["input", "agent_scratchpad"],
            ),
        ],
    )

    callbacks = get_callback_handlers(logpath)
    agent = ZeroShotAgent(
        llm_chain=LLMChain(llm=llm, prompt=prompt, callbacks=callbacks, verbose=True),
        allowed_tools=[tool.name for tool in tools],
    )

    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True,
        callbacks=callbacks,
        handle_parsing_errors=True,
    )
    return agent_executor.run(command)


@dataclass
class SmartThingsPlannerToolConfig(BaseToolConfig):
    _target: Type = field(default_factory=lambda: SmartThingsPlannerTool)
    name: str = "api_usage_planner"

    # 用于生成执行某条指令所需的 API 调用计划。该工具的输入内容为用户的自然语言指令。务必将原始用户指令传递给该工具，以提供完整的上下文信息。
    description: str = "Used to generate a plan of api calls to make to execute a command. The input to this tool is the user command in natural language. Always share the original user command to this tool to provide the overall context."
    llm_config: LLMConfig = None


class SmartThingsPlannerTool(SAGEBaseTool):
    chain: LLMChain = None
    logpath: str = None

    def setup(self, config: SmartThingsPlannerToolConfig):
        if isinstance(config.llm_config, TGIConfig):
            config.llm_config = TGIConfig(stop_sequences=["Human", "<FINISHED>"])
        llm = config.llm_config.instantiate()
        self.logpath = config.global_config.logpath
        # dm = DocManager.from_json(config.global_config.docmanager_cache_path)
        # (
        #     one_liners_string,
        #     device_capability_string,
        # ) = dm.capability_summary_for_devices()
        # TODO 考虑怎么改吧
        # one_liners_string=DEVICE_INFO_DOC.all_capabilities_str
        # device_capability_string=DEVICE_INFO_DOC.device_info_strings
        # TODO
        one_liners_string=DEVICE_INFO_DOC.entity_info_strings
        device_capability_string=DEVICE_INFO_DOC.entity_capabilities_strings

        prompt = ChatPromptTemplate.from_messages(
            [
                # - Restate the query 3 different ways
                SystemMessage(
                    content=f"""
You are a planner that helps users interact with their smart devices.
You are given a list of high level summaries of entity capabilities ("all capabilities:").
You are also given a list of available entities ("entities you can use") which will tell you the name and entity_id of the entity, as well as listing which capabilities the entity has.
Your job is to figure out the sequence of which entities and capabilities to use in order to execute the user's command.

Follow these instructions:
- Include entity_ids (guid strings), capability ids, and explanations of what needs to be done in your plan.
- The capability information you receive is not detailed. Often there will be multiple capabilities that sound like they might work. You should list all of the ones that might work to be safe.
- Don't always assume the devices are already on.

all capabilities:
{one_liners_string}

devices you can use:
{device_capability_string}

Use the following format:
Device Ids: list of relevant devices IDs and names
Capabilities: list of relevant capabilities
Plan: steps to execute the command
Explanation: Any further explanations and notes
<FINISHED>
"""
                ),
                HumanMessagePromptTemplate.from_template(
                    "{query}.",
                    input_variables=["query"],
                ),
            ],
        )

        callbacks = get_callback_handlers(self.logpath)
        self.chain = LLMChain(llm=llm, prompt=prompt, callbacks=callbacks, verbose=True)

    def _run(self, command) -> str:
        # try:
        #    json.loads(command)
        # The LLM fails to give the command in natural language
        #    return "The command should be in natural language and not a json."
        # except json.decoder.JSONDecodeError:
        return self.chain.run(command)

# ==============================================

# 模拟数据的文件所在目录
mock_data_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),  # 当前文件所在目录
    'test_mock_data'  # 子目录（无开头斜杠）
)
token=os.getenv("HOMEASSITANT_AUTHORIZATION_TOKEN")
server=os.getenv("HOMEASSITANT_SERVER")
active_project_env=os.getenv("ACTIVE_PROJECT_ENV")

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
@dataclass
class get_all_entity_idToolConfig(BaseToolConfig):
    _target: Type = field(default_factory=lambda: get_all_entity_idTool)
    name: str = "get_all_entity_id"
    description: str = """Returns an array of state objects.
    Each state has the following attributes: entity_id, state, last_changed and attributes."""

class get_all_entity_idTool(SAGEBaseTool):
    def _run(self, *args: Any, **kwargs: Any) -> Any:
        if active_project_env == "dev":
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
            return response.json()
        elif active_project_env == "test":
            file_path = os.path.join(mock_data_dir, 'selected_entities.json')
            with open(file_path, 'r', encoding='utf-8') as f:
                # 解析JSON文件并返回Python对象
                return json.load(f)

@dataclass
class get_services_by_domainToolConfig(BaseToolConfig):
    _target: Type = field(default_factory=lambda: get_services_by_domainTool)
    name: str = "get_services_by_domain"
    description: str = """return all services included in the domain.Input to the tool should be a json string with 1 keys:
domain (str)"""

class get_services_by_domainTool(SAGEBaseTool):
    def _run(self, text: str) -> Any:
        exec_spec = parse_json(text)

        if exec_spec is None:
            return "Invalid input format. Input to the get_services_by_domain tool should be a json string with 1 keys: domain (str)."

        if isinstance(exec_spec, list):
            if len(exec_spec) == 1:
                exec_spec = exec_spec[0]
            else:
                return "Invalid usage: input to this tool should be a dict, not a list"

        domain = exec_spec["domain"]

        if active_project_env == "dev":
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
@dataclass
class get_states_by_entity_idToolConfig(BaseToolConfig):
    _target: Type = field(default_factory=lambda: get_states_by_entity_idTool)
    name: str = "get_states_by_entity_id"
    description: str = """Returns a state object for specified entity_id.
    Returns 404 if not found.Input to the tool should be a json string with 1 keys:
    entity_id (str)"""

class get_states_by_entity_idTool(SAGEBaseTool):
    def _run(self, text: str) -> Any:
        exec_spec = parse_json(text)

        if exec_spec is None:
            return "Invalid input format. Input to the get_services_by_domain tool should be a json string with 1 keys: entity_id (str)."

        if isinstance(exec_spec, list):
            if len(exec_spec) == 1:
                exec_spec = exec_spec[0]
            else:
                return "Invalid usage: input to this tool should be a dict, not a list"

        entity_id = exec_spec["entity_id"]

        if active_project_env == "dev":
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
            return response.json()
        elif active_project_env == "test":
            file_path = os.path.join(mock_data_dir, 'selected_entities.json')
            return extract_entity_by_id(file_path, entity_id)
@dataclass
class execute_domain_service_by_entity_idToolConfig(BaseToolConfig):
    _target: Type = field(default_factory=lambda: execute_domain_service_by_entity_idTool)
    name: str = "execute_domain_service_by_entity_id"
    description: str = """
    Calls a service within a specific domain. Will return when the service has been executed.

    Returns a list of states that have changed while the service was being executed, and optionally response data, if supported by the service.
    Input to the tool should be a json string with 3 keys:
    domain (str)
    service (str)
    body (str)
    
    Additional notes on the body: The value of 'Content-Type' must be 'application/json'. The body must contain at least the 'entity_id' (and there must be exactly one 'entity_id' in the body). If the service requires additional parameters, please provide them accordingly.
    """
class execute_domain_service_by_entity_idTool(SAGEBaseTool):
    def _run(self, text: str) -> Any:
        exec_spec = parse_json(text)

        if exec_spec is None:
            return "Invalid input format. Input to the get_services_by_domain tool should be a json string with 1 keys: entity_id (str)."

        if isinstance(exec_spec, list):
            if len(exec_spec) == 1:
                exec_spec = exec_spec[0]
            else:
                return "Invalid usage: input to this tool should be a dict, not a list"

        domain = exec_spec["domain"]
        service = exec_spec["service"]
        body = exec_spec["body"]
        if active_project_env == "dev":
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
            return response.json()

@dataclass
class SmartThingsToolConfig(BaseToolConfig):
    _target: Type = field(default_factory=lambda: SmartThingsTool)
    name: str = "smartthings_tool"

    # 使用此工具与 SmartThings（智能设备平台）进行交互。该工具支持接收自然语言指令，且不得遗漏原始指令中的任何细节。可借助此工具确定哪台设备能够实现该查询需求。
    # 将平台名称改为homeassitant
    description: str = """
Use this to interact with homeassitant. Accepts natural language commands. Do not omit any details from the original command. Use this tool to determine which device can accomplish the query.
"""

    llm_config: LLMConfig = None
    tool_configs: tuple[BaseConfig, ...] = (

        SmartThingsPlannerToolConfig(),
        get_all_entity_idToolConfig(),
        get_services_by_domainToolConfig(),
        get_states_by_entity_idToolConfig(),
        execute_domain_service_by_entity_idToolConfig(),



        # ApiDocRetrievalToolConfig(),
        # GetAttributeToolConfig(),
        # ExecuteCommandToolConfig(),
        # DeviceDisambiguationToolConfig(),
    )


class SmartThingsTool(SAGEBaseTool):
    llm: BaseChatModel = None
    logpath: str = None

    def setup(self, config: SmartThingsToolConfig):
        if isinstance(config.llm_config, TGIConfig):
            config.llm_config = TGIConfig(stop_sequences=["Human", "<FINISHED>"])

        self.llm = config.llm_config.instantiate()
        self.logpath = config.global_config.logpath

    def _run(self, command) -> Any:
        # TODO 什么时候设置好的  self.tools ？？！
        return create_and_run_smartthings_agent_v2(
            command, self.llm, self.logpath, self.tools
        )
