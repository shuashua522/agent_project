import os
from langchain.chat_models import init_chat_model
import configparser
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from abc import ABC, abstractmethod

class BaseToolAgent(ABC):

    def __init__(self,provider="doubao"):
        self.provider=provider
    @staticmethod
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

    @abstractmethod
    def get_tools(self):
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