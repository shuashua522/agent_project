import uuid
from typing import Annotated, List, Callable

from langgraph.graph import MessagesState

from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm



from abc import abstractmethod
from langchain_core.tools import tool

from agent_project.agentcore.smart_home_agent.queueBased_scheduler import generateTaskToQueueTool
from agent_project.agentcore.smart_home_agent.saveOrSearch_local_condition_funcs_agent import \
    search_local_contionalCode_tool, save_func_code_to_file
from agent_project.agentcore.smart_home_agent.test_with_baselines.baselines_homeassitant.sage.smart.smartThings import \
    get_all_entity_id, get_states_by_entity_id


class GenerateConditionCode(BaseToolAgent):
    def get_tools(self):
        tools = [get_all_entity_id,
                 get_states_by_entity_id,
                 save_func_code_to_file,
                 ]
        return tools

    def call_tools(self, state: MessagesState):
        """
            :param condition:
            :return:
            """
        uuid_str = str(uuid.uuid4()).replace("-", "_")
        system_prompt = """
            
            请根据用户需求生成无参的Python函数，函数名固定为{func_name}，函数形如：
            def {func_name}()-> bool:

            用户的需求一般是让检查设备的状态是否满足条件：
            1. 你需要确定是检查哪些设备，这一步可以通过调用@tool get_all_entity_id确定；
            2. 你需要生成代码来检查相应的设备是否满足条件，如果满足，就返回true。这一步你可以通过@tool get_states_by_entity_id返回的状态进行条件判断;
            如果你不清楚返回的状态包含什么内容，你可以先调用@tool get_states_by_entity_id观察,每个entity_id最多调用一次。

            - 你不应该在生成代码中调用get_all_entity_id，因为其是为了让你确定设备的entity_id用的；确定完entity_id后，调用get_states_by_entity_id不是就能获得需要的状态信息了
            - 提供给你的tools，你可以像本地函数一样在代码中调用，例如想在代码中调用@tool calculate_area:
            print(get_all_entity_id())

            生成代码要求：
            - 必须正确调用上述工具，参数类型要匹配
            - 代码需要有注释，说明逻辑
            - 处理可能的异常（如半径为负数的情况）
            - 必须添加文档注释符说明函数用途

            **生成代码后，调用@tool save_func_code_to_file将其保存到本地函数库中**
            - 只要调用@tool save_func_code_to_file没有报错，就是保存成功
            - 不要反复调用@tool save_func_code_to_file，
            - 保存到函数库里，该结束就结束，不要多次写代码，然后调用@tool save_func_code_to_file，
            
            最后！！！！>>>返回格式：仅返回纯Python代码！！！
            """.format(func_name="func"+uuid_str)
        llm = get_llm().bind_tools(self.get_tools())
        system_message = {
            "role": "system",
            "content": system_prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        print(response.content)
        return {"messages": [response]}

@tool
def generateConditionCodeTool(condition_statement: Annotated[str, "需要检查的条件，自然语言描述;比如卧室的光照是否充足"]):
    """
    生成一个python函数，用于检查条件{condition_statement}是否已满足
    :return: python函数字符串
    """
    return GenerateConditionCode().run_agent(condition_statement)

class PersistentCommandAgent(BaseToolAgent):
    def get_tools(self) -> List[Callable]:
        tools=[generateConditionCodeTool,
               generateTaskToQueueTool,
               search_local_contionalCode_tool]
        return tools

    def call_tools(self, state: MessagesState):
        system_prompt = """
            调用工具以实现持久化监听用户的指令
        """
        llm = get_llm().bind_tools(self.get_tools())
        system_message = {
            "role": "system",
            "content": system_prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        print(response.content)
        return {"messages": [response]}

@tool
def persistentCommandTool(task: Annotated[str, "需要持久监控的任务描述"])->str:
    """
        能够根据任务描述，持久化监控。
        :示例1:
            task="当网络关闭时，通过我":
        :示例2:
            task="每周日，汇报本周智能家居设备使用情况"
        :示例3:
            task="每隔一个小时，读取传感器数据，存入数据库"
    """
    return PersistentCommandAgent().run_agent(task)

if __name__ == "__main__":
    # task="每隔一天，检查光照是否充足"
    # task="当门窗打开时，关闭空调"
    # task="当插座关闭时，邮件通知我"
    # PersistentCommandAgent().run_agent(task)
    # task="光照是否充足"
    # GenerateConditionCode().run_agent(task)
    pass