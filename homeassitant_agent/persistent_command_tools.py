from typing import Annotated

from langgraph.graph import MessagesState

from agent_project.homeassitant_agent.base_agent import BaseToolAgent
from agent_project.homeassitant_agent.homeassitant_agent import get_all_entity_id, get_states_by_entity_id
from abc import abstractmethod
from langchain_core.tools import tool


class GenerateConditionCode(BaseToolAgent):
    def get_tools(self):
        tools = [get_all_entity_id, get_states_by_entity_id]
        return tools

    def call_tools(self, state: MessagesState):
        """
            :param condition:
            :return:
            """
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

            返回格式：仅返回纯Python代码！！！
            """.format(func_name="func")
        llm = self.get_llm("doubao").bind_tools(self.get_tools())
        system_message = {
            "role": "system",
            "content": system_prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        print(response.content)
        return {"messages": [response]}
    @staticmethod
    @tool
    def generateConditionCodeTool(condition_statement: Annotated[str, "需要检查的条件，自然语言描述;比如卧室的光照是否充足"]):
        """
        生成一个python函数，用于检查条件{condition_statement}是否已满足
        :return: python函数字符串
        """
        return GenerateConditionCode().run_agent(condition_statement)


# f1(problem)->f2(condition,then_todo,schedule_statement)

# print(GenerateConditionCode.generateConditionCodeTool("插座是否打开"))


