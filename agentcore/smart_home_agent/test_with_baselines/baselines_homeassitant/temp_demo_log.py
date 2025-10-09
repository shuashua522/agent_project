import os
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain.callbacks import FileCallbackHandler
from agent_project.agentcore.config.global_config import MODEL, BASE_URL, API_KEY, PROXIES, PROVIDER
from langchain.chat_models import init_chat_model

def get_llm():

    provider=PROVIDER
    model = MODEL
    base_url = BASE_URL
    api_key = API_KEY

    llm = None
    if (provider == "openai"):
        proxies = PROXIES
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
# --------------------------
# 关键：配置本地日志文件
# --------------------------
log_file = "langgraph_local.log"
file_handler = FileCallbackHandler(log_file)  # LangChain 内置的文件日志处理器

# --------------------------
# 定义状态和节点
# --------------------------
class AgentState(State):
    messages: list

# LLM 调用时传入日志处理器
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    callbacks=[file_handler]  # 自动记录 LLM 交互到文件
)

def call_llm(state: AgentState) -> AgentState:
    response = llm.invoke(state.messages)
    return AgentState(messages=state.messages + [response])

# --------------------------
# 构建图时添加全局日志（可选）
# --------------------------
graph_builder = StateGraph(AgentState)
graph_builder.add_node("call_llm", call_llm)
graph_builder.add_edge(START, "call_llm")
graph_builder.add_edge("call_llm", END)

# 编译图时传入日志处理器（记录节点执行）
graph = graph_builder.compile(callbacks=[file_handler])

# 测试运行
graph.invoke(AgentState(messages=[{"role": "user", "content": "什么是 LangGraph？"}]))
print(f"日志已保存到 {os.path.abspath(log_file)}")
