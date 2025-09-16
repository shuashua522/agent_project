import os
from typing import Callable, List

from langchain.chat_models import init_chat_model
import configparser
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from abc import ABC, abstractmethod

class BaseToolAgent(ABC):

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

        tool_node = ToolNode(tools)
        builder.add_node("call_tools",self.call_tools)
        builder.add_node("tools", tool_node)

        builder.add_edge(START, "call_tools")
        builder.add_conditional_edges("call_tools", self.should_continue, ["tools", END])
        builder.add_edge("tools", "call_tools")

        # 编译图为可运行的代理
        agent = builder.compile()
        return agent
    def run_agent(self,problem):
        agent=self.create_agent()
        last_message = None  # 初始化最后一个消息变量

        for step in agent.stream(
                {"messages": [{"role": "user", "content": problem}]},
                stream_mode="values",
        ):
            last_message = step["messages"][-1]  # 更新最后一个消息
            # 如果你不需要打印中间步骤，可以移除下面这行
            last_message.pretty_print()
        return last_message.content