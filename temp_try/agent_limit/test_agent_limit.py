import os
from contextlib import redirect_stdout
from io import StringIO
from typing import Callable, List
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
import configparser
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from abc import ABC, abstractmethod

from agent_project.agentcore.commons.diy_ToolNode import SerialToolNode
from agent_project.agentcore.commons.utils import get_llm


class BaseToolAgent(ABC):
    def __init__(self,logger=None):
        self.logger=logger

    @abstractmethod
    def get_tools(self)-> List[Callable]:
        pass
    @abstractmethod
    def call_tools(self,state: MessagesState):
        """
        demo:
        llm = self.get_llm("doubao").bind_tools(self.get_tools())
            messages = state["messages"]
            response = llm.invoke(messages)
            return {"messages": [response]}
        """
        pass

    def should_continue(self,state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    def create_agent(self):
        # 构建状态图
        builder = StateGraph(MessagesState)  # 以消息状态作为图的核心状态

        tools=self.get_tools()

        tool_node = SerialToolNode(tools)

        builder.add_node("call_tools",self.call_tools)
        builder.add_node("tools", tool_node)

        builder.add_edge(START, "call_tools")
        builder.add_conditional_edges("call_tools", self.should_continue, ["tools", END])
        builder.add_edge("tools", "call_tools")

        # 编译图为可运行的代理
        agent = builder.compile()
        agent = agent.with_config({"recursion_limit": 3})
        return agent
    def run_agent(self,problem,):
        agent=self.create_agent()
        last_message = None  # 初始化最后一个消息变量

        import agent_project.agentcore.config.global_config as global_config
        for step in agent.stream(
                {"messages": [{"role": "user", "content": problem}]},
                stream_mode="values",
                config={
                    "tags": [global_config.LANGSMITH_TAG_NAME],
                    # "metadata": {
                    #     "user_id": "user_123",
                    #     "session_id": "session_456",
                    #     "environment": "production"
                    # }
                },
        ):
            last_message = step["messages"][-1]  # 更新最后一个消息
            if not hasattr(self, 'logger') or self.logger is None:
                import agent_project.agentcore.config.global_config as global_config
                self.logger = global_config.GLOBAL_AGENT_DETAILED_LOGGER
            if self.logger != None:
                # 捕获 pretty_print() 的输出内容
                # 创建一个字符串缓冲区用于捕获输出
                buffer = StringIO()
                # 重定向标准输出到缓冲区
                with redirect_stdout(buffer):
                    last_message.pretty_print()  # 此时输出会被捕获到buffer
                # 获取捕获的内容（去除末尾可能的空行）
                output = buffer.getvalue().rstrip('\n')

                # 1. 输出到控制台（保持原有的打印效果）
                print(output)
                # 2. 输出到日志（使用logger记录捕获的内容）
                self.logger.info(output)
            else:
                last_message.pretty_print()


        return last_message.content

@tool
def add(a,b):
    """求a与b之和"""
    return a+b
class TestLimitAgent(BaseToolAgent):
    def get_tools(self) -> List[Callable]:
        tools=[add]
        return tools

    def call_tools(self, state: MessagesState):
        system_prompt = """
                   利用给定工具解决用户问题
               """
        llm = get_llm().bind_tools(self.get_tools())
        system_message = {
            "role": "system",
            "content": system_prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        print(response.content)
        return {"messages": [response]}

if __name__ == "__main__":
    # TestLimitAgent().run_agent("计算5+6=?，然后计算99+前面的5+6的结果")
    llm=get_llm()
    print(llm.invoke("写一篇100字的日记").content)