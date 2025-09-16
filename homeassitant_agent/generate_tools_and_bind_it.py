import re

from langchain_core.tools import StructuredTool
import os
from langchain.chat_models import init_chat_model
import configparser
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.tools import tool
from langgraph.types import Command
from typing import Literal
from langchain_core.messages import AIMessage

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "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"
def remove_thinks(text):
    # 匹配 <think> 和 </think> 之间的所有内容（包括标签）
    # .*? 表示非贪婪匹配，确保只匹配到最近的 </think>
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

def get_llm(provider):
    # 创建配置解析器对象
    config = configparser.ConfigParser()
    # 读取INI文件
    config.read('my_config.ini', encoding='utf-8')
    # 设置LangSmith跟踪开关和API密钥
    # os.environ["LANGSMITH_TRACING"] = config.get('LangSmith', 'langsmith_tracing')
    # os.environ["LANGSMITH_API_KEY"] = config.get('LangSmith', 'langsmith_api_key')

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

common_tools=[]

@tool
def load_function_from_string(func_code: str, func_name: str)->str:
    """
    从字符串加载函数

    参数:
        func_code: 包含函数定义的字符串
        func_name: 要提取的函数名
    """
    # if func_name=="add":
    #     return "已存在同名函数"
    # 创建一个字典来存储动态执行的代码中的对象
    global_namespace = {}

    # 执行函数代码字符串
    exec(func_code, global_namespace)

    # 从命名空间中获取函数
    if func_name in global_namespace:
        func=global_namespace[func_name]
        new_tool = StructuredTool.from_function(func=func)
        common_tools.append(new_tool)
        print(common_tools)
        return "已成功执行"
    else:
        raise ValueError(f"函数 {func_name} 未在提供的代码中定义")


load_code_tools=[load_function_from_string]
tool_node = ToolNode(load_code_tools)
def generate_tool_code_by_llm(state: MessagesState):
    """
    让LLM根据功能描述，生成一个函数代码，最后转化为工具以复用
    """
    llm = get_llm("doubao").bind_tools(load_code_tools, tool_choice="load_function_from_string")
    # 提示词：强制LLM生成规范的BaseTool子类，包含必要属性和方法
    prompt = f"""
        请调用tools生成Python函数，满足用户提出的功能

        假设需满足功能求两个数相加，调用工具load_function_from_string，参数func_name="add",func_code=
        def add(a: float, b: float) -> float:
            \"\"\"
            计算两个数的和

            参数:
                a: 第一个加数
                b: 第二个加数

            返回:
                两个数的和
            \"\"\"
            return a + b
        """
    system_message = {
        "role": "system",
        "content": "请调用tools生成Python函数，满足用户提出的功能。并根据tools调用结果的反馈修正代码或者函数名",
    }
    response = llm.invoke([system_message]+state["messages"])
    return {"messages": [response]}

def check_output(state: MessagesState) -> Command[Literal["generate_tool_code", END]]:
    code_output = state["messages"][-1].content
    check_result_system_prompt = """
    【代码运行结果】：{code_output}

    请你担任结果校验者，判断"代码运行结果"是否出现异常，并按照以下输出规则：
       - 运行成功，无报错、无异常，仅输出：ok
       - 运行出现问题，仅输出：error

    示例：
    【代码运行结果】：已成功执行
    返回：ok

    output:
    ok
    """.format(code_output=code_output)
    system_message = {
        "role": "system",
        "content": check_result_system_prompt,
    }

    llm=get_llm("doubao")
    # 调用模型检查
    response = llm.invoke([system_message])

    cleaned_content = remove_thinks(response.content)
    is_ok = ("ok" in cleaned_content) or ("null" in cleaned_content) or (
                cleaned_content.isspace() or cleaned_content == "")

    if is_ok:
        goto = END
        return Command(
            # this is the state update
            # update={"messages": [response]},
            # this is a replacement for an edge
            goto=goto,
        )
    else:
        goto = "generate_tool_code"
        # response = AIMessage(f"Issues exist in the code's running result: {cleaned_content}")  # 格式化结果消息
        return Command(
            # this is the state update
            # update={"messages": [response]},
            # this is a replacement for an edge
            goto=goto,
        )


builder = StateGraph(MessagesState)

# Define the two nodes we will cycle between
builder.add_node("generate_tool_code", generate_tool_code_by_llm)
builder.add_node("tools", tool_node)
builder.add_node("check_output", check_output)

builder.add_edge(START, "generate_tool_code")
builder.add_edge("generate_tool_code", "tools")
builder.add_edge("tools", "check_output")

agent = builder.compile()

def func(problem):
    last_message = None  # 初始化最后一个消息变量

    for step in agent.stream(
            {"messages": [{"role": "user", "content": problem}]},
            stream_mode="values",
    ):
        last_message = step["messages"][-1]  # 更新最后一个消息
        # 如果你不需要打印中间步骤，可以移除下面这行
        last_message.pretty_print()

func("求两个数相加")
func("求两个数相乘")
llm=get_llm("deepseek")
print(common_tools)
llm_with_tools = llm.bind_tools(common_tools)
print(llm_with_tools.invoke("请计算 123 加上 456 等于多少？"))

# 可以放在每个需要编程的地方
# 不用考虑工具累积越来越多

# 修改为持久化保存，方便删除
# 两个agent合并起来有没有问题












llm=get_llm("doubao")
prompt = """
        你是一个智能家居助手，你的功能是将用户的提问拆解为两部分，一部分是条件，另一部分是当条件满足时要执行的动作，返回一个JSON格式的文本。
        
        例如用户提问【当书柜旁的电视关掉时，打开床边的灯】，返回：
        {
        "if":书柜旁的电视关掉
        "then":打开床边的灯
        }
        """
system_message = {
    "role": "system",
    "content": prompt,
}
problem="我接到电话时，调整电视的音量。"
user_message = {"role": "user", "content": problem}
response = llm.invoke([system_message,user_message])
print(response.content)