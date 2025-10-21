from typing import List, Callable

from langchain_core.tools import tool, StructuredTool
from langgraph.graph import MessagesState

from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm
from agent_project.agentcore.smart_home_agent.device_interaction_agent import deviceInteractionTool
from agent_project.agentcore.smart_home_agent.persistent_command_agent import persistentCommandTool
from agent_project.agentcore.smart_home_agent.privacy_handler import ResultDecodeAgent


class SmartHomeAgent(BaseToolAgent):
    def get_tools(self) -> List[Callable]:
        tools=[deviceInteractionTool,
               persistentCommandTool]
        return tools

    def call_tools(self, state: MessagesState):
        system_prompt = """
            你是一名智能家居助手，调用工具以满足用户需求。
            - 需要注意的是由于智能家居中的一些数据已经进行隐私处理，数据会被加密。因此，如果调用工具后的结果包含加密文本，无需在意，后续我会处理的。
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
def smart_home_agent_tool(problem:str):
    """
    传入需要执行的智能家居任务{problem}；本工具会根据{problem}描述的任务完成对应操作。
    :param problem: 自然语言描述
    """
    encoed_str=SmartHomeAgent().run_agent(problem)
    return ResultDecodeAgent().run_agent(encoed_str)

if __name__ == "__main__":
    decoe_str = SmartHomeAgent().run_agent("网络状况")
    ResultDecodeAgent().run_agent(decoe_str)
    # SmartHomeAgent().run_agent("每隔一天，检查光照是否充足")
    pass