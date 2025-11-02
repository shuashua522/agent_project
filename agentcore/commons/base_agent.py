import os
from contextlib import redirect_stdout
from io import StringIO
from typing import Callable, List

from langchain.chat_models import init_chat_model
import configparser
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from abc import ABC, abstractmethod

from agent_project.agentcore.commons.diy_ToolNode import SerialToolNode


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
        # agent = agent.with_config({"recursion_limit": 5})
        return agent
    def run_agent(self,problem,):
        agent=self.create_agent()
        last_message = None  # 初始化最后一个消息变量

        for step in agent.stream(
                {"messages": [{"role": "user", "content": problem}]},
                stream_mode="values",
                config={
                    "tags": ["02_try"],
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


# if self.logger == None:
#     self.logger = GLOBAL_AGENT_DETAILED_LOGGER
# if self.logger != None:
#     log_message = ""
#     if last_message.content:
#         log_message = f"{last_message.type}: {last_message.content}"
#     elif hasattr(last_message, "tool_calls") and last_message.tool_calls:
#         # 提取工具调用信息（工具名 + 参数）
#         tool_calls = []
#         for tool in last_message.tool_calls:
#             tool_name = tool.get("name", "未知工具")
#             tool_args = tool.get("args", {})
#             tool_calls.append(f"{tool_name}({tool_args})")
#
#         # 生成工具调用日志
#         log_message = f"{last_message.type}:tool_call: {', '.join(tool_calls)}"
#     self.logger.info(log_message)  # 记录到日志