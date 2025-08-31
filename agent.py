import os
import sys
from io import StringIO
import subprocess

import configparser
# 创建配置解析器对象
config = configparser.ConfigParser()
# 读取INI文件
config.read('my_config.ini', encoding='utf-8')
sections = config.sections()  # 获取所有section

# 设置LangSmith跟踪开关和API密钥
os.environ["LANGSMITH_TRACING"] = config.get('LangSmith', 'langsmith_tracing')
os.environ["LANGSMITH_API_KEY"] = config.get('LangSmith', 'langsmith_api_key')

import os
from langchain.chat_models import init_chat_model
provider="openai"
model=config.get(provider, 'model')
base_url=config.get(provider, 'base_url')
api_key=config.get(provider, 'api_key')

llm = None
if(provider=="openai"):
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
        api_key=os.environ.get("ARK_API_KEY"),
        base_url=base_url,
        temperature=0,
    )

from typing import Literal
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

def generate_python_code(state: MessagesState):
    # 生成查询语句的节点逻辑
    generate_python_code_system_prompt = """
    你是一个用Python来解决问题的代理。
    给定输入问题，直接生成对应的Python代码或者根据反馈意见重新生成代码。

    - 直接输出Python代码，不要添加任何不符合Python代码的文本，你的回答我会直接存储到.py文件。
    - 不要添加任何解释性文字，除非带了注释
    - 编写代码时，如需输出结果，请使用print
    """
    system_message = {
        "role": "system",
        "content": generate_python_code_system_prompt,
    }
    response = llm.invoke([system_message] + state["messages"])

    python_code_system_prompt = """
        【文本】：{text}
        检查【文本】内容是否可以直接写入.py文件，如果可以，直接输出原文本；
        如果不行，修改【文本】成可以直接写入 .py文件的形式，然后直接输出它（**不要附加任何不符合Python语法的内容**）
        """.format(text=response.content)
    system_message = {
        "role": "system",
        "content": python_code_system_prompt,
    }
    response = llm.invoke([system_message])

    return {"messages": [response]}


from bandit_use01 import run_bandit_cmd
from import_validator import extract_imports,run_import_check

def sanitize_input(query: str) -> str:
    query = re.sub(r"^(\s|`)*(?i:python)?\s*", "", query)
    query = re.sub(r"(\s|`)*$", "", query)
    return query
def check_python_code(state: MessagesState) -> Command[Literal["generate_python_code", "run_python_code"]]:
    messages = state["messages"]
    code = messages[-1].content
    code=sanitize_input(code)
    # 保存到 my_code.py 文件
    with open("agent_generate_code/my_code.py", "w", encoding="utf-8") as f:
        f.write(code)

    valida_imports=extract_imports("agent_generate_code/my_code.py", "agent_generate_code/import_try.py")
    success, message = run_import_check("agent_generate_code/import_try.py")

    if not success:
        goto = "generate_python_code"
        response = AIMessage(f"The module does not exist. Use another module or install the module first before importing and using it.details: {message}")  # 格式化结果消息
        return Command(
            # this is the state update
            update={"messages": [response]},
            # this is a replacement for an edge
            goto=goto,
        )


    check_result = run_bandit_cmd(r'agent_generate_code/my_code.py', output_format='json')

    # 生成查询语句的节点逻辑
    check_system_prompt = """
    【代码】：{code}
    【安全检查结果】：{check_result}

    请你担任结果校验者，判断安全检查结果是否存在问题，并按照以下输出规则（**必须生成判断结果，不得返回空内容**）：
       - 符合预期时，仅输出：ok
       - 不符合预期时，仅输出error
    """.format(code=code, check_result=check_result)

    system_message = {
        "role": "system",
        "content": check_system_prompt,
    }
    response = llm.invoke([system_message])
    is_ok = "ok" in response.content
    is_ok=True

    if is_ok:
        goto = "run_python_code"
        return Command(
            # # this is the state update
            # update={"messages": [response]},
            # this is a replacement for an edge
            goto=goto,
        )
    else:
        goto = "generate_python_code"
        response = AIMessage(f"Code check result: {check_result}")  # 格式化结果消息
        return Command(
            # this is the state update
            update={"messages": [response]},
            # this is a replacement for an edge
            goto=goto,
        )


def run_python_code(state: MessagesState) -> Command[Literal["generate_python_code", "check_output_val"]]:
    messages = state["messages"]
    code = messages[-1].content
    run_result=None
    is_ok=True
    try:
        result = subprocess.run(
            ["python", "agent_generate_code/my_code.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            # 注意：这里不设置check=True，手动处理返回码
        )
        # 手动检查返回码
        if result.returncode == 0:
            run_result=result.stdout
        else:
            is_ok=False
            run_result=result.stderr
    except Exception as e:
        is_ok=False
        run_result=e

    if is_ok:
        goto = "check_output_val"
        response = AIMessage(f"Code run result: {run_result}")  # 格式化结果消息
        return Command(
            # this is the state update
            update={"messages": [response]},
            # this is a replacement for an edge
            goto=goto,
        )
    else:
        goto = "generate_python_code"
        response = AIMessage(f"Code run result: {run_result}")  # 格式化结果消息
        return Command(
            # this is the state update
            update={"messages": [response]},
            # this is a replacement for an edge
            goto=goto,
        )


import re


def remove_thinks(text):
    # 匹配 <think> 和 </think> 之间的所有内容（包括标签）
    # .*? 表示非贪婪匹配，确保只匹配到最近的 </think>
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

def check_output_val(state: MessagesState) -> Command[Literal["generate_python_code", END]]:
    messages = state["messages"]
    check_result_val_isValid_system_prompt = """
    【问题】：{question}
    【答案】：{ans}

    请你担任结果校验者，判断答案是否符合预期，并按照以下输出规则（**必须生成判断结果，不得返回空内容，符合就输出ok**）：
       - 符合预期时，仅输出：ok
       - 不符合预期时，仅输出具体原因
    
    如果当前任务属于计算任务，只需判断答案是否为数字

    示例：
    【问题】：北京的昨天气温？
    【答案】：26摄氏度

    output:
    ok
    """.format(ans=messages[-1].content, question=messages[0].content)
    system_message = {
        "role": "system",
        "content": check_result_val_isValid_system_prompt,
    }
    # 调用模型检查
    response = llm.invoke([system_message] + state["messages"])
    cleaned_content = remove_thinks(response.content)
    is_ok = "ok" in cleaned_content

    if is_ok:
        goto = END
        return Command(
            # this is the state update
            # update={"messages": [response]},
            # this is a replacement for an edge
            goto=goto,
        )
    else:
        goto = "generate_python_code"
        response = AIMessage(f"Issues exist in the code's running result: {cleaned_content}")  # 格式化结果消息
        return Command(
            # this is the state update
            update={"messages": [response]},
            # this is a replacement for an edge
            goto=goto,
        )


# 构建状态图
builder = StateGraph(MessagesState)  # 以消息状态作为图的核心状态

# 添加节点（每个节点对应一个处理步骤）
builder.add_node(generate_python_code)
builder.add_node(check_python_code)
builder.add_node(run_python_code)
builder.add_node(check_output_val)

# 定义节点间的边
builder.add_edge(START, "generate_python_code")
builder.add_edge("generate_python_code", "check_python_code")

# 编译图为可运行的代理
agent = builder.compile()

# question = "求解:$[ (3.5 + 4.2)^2 - 12.5 \times 3.6 ] \div (7.8 - 2.3) + 4^3$"
#
# for step in agent.stream(
#         {"messages": [{"role": "user", "content": question}]},
#         stream_mode="values",
# ):
#     step["messages"][-1].pretty_print()
def remove_code_run_prefix(s):
    prefix = "Code run result: "
    if s.startswith(prefix):
        return s[len(prefix):].lstrip()  # 使用 lstrip() 移除剩余的前导空白字符
    return s  # 如果字符串不以该前缀开头，则原样返回
def func(problem):
    last_message = None  # 初始化最后一个消息变量

    for step in agent.stream(
            {"messages": [{"role": "user", "content": problem}]},
            stream_mode="values",
    ):
        last_message = step["messages"][-1]  # 更新最后一个消息
        # 如果你不需要打印中间步骤，可以移除下面这行
        last_message.pretty_print()

    return remove_code_run_prefix(last_message.content)  # 返回最后一个消息

# func("广东时间")