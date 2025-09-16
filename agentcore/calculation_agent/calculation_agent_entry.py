import os
import sys
from io import StringIO
import subprocess
import configparser
import os
from langchain.chat_models import init_chat_model
from typing import Literal, List, Callable
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
import re
from pathlib import Path

from agent_project.agentcore.calculation_agent.bandit_security_check import run_bandit_cmd
from agent_project.agentcore.calculation_agent.generate_tools_to_commons import generate_reusable_functions_tool
from agent_project.agentcore.calculation_agent.import_validator import extract_imports, run_import_check
from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm
from agent_project.agentcore.config.global_config import PROVIDER, COMMON_TOOLS


class CodeCalculationAgent:
    # 类的初始化方法（构造函数）
    def __init__(self):
        # 实例属性
        self.provider=PROVIDER
        self.llm=get_llm()
        # self.code_file=f"agent_generate_code/{provider}_code.py"
        # self.import_file=f"agent_generate_code/{provider}_import_try.py"
        # 获取当前文件所在目录的绝对路径
        current_dir = Path(__file__).resolve().parent
        # 拼接代码目录路径
        self.code_dir = current_dir / "agent_generate_code"
        # 创建目录（如果不存在）
        self.code_dir.mkdir(exist_ok=True)
        # 拼接出完整的绝对路径
        self.code_file = current_dir / f"agent_generate_code/{self.provider}_code.py"
        self.code_file = str(self.code_file)# 拼接出完整的绝对路径

        self.import_file = current_dir / f"agent_generate_code/{self.provider}_import_try.py"
        self.import_file = str(self.import_file)


    def generate_python_code(self,state: MessagesState):

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
        response = self.llm.invoke([system_message] + state["messages"])

        python_code_system_prompt = """
            【文本】：{text}
            检查【文本】内容是否可以直接写入.py文件，如果可以，直接输出原文本；
            如果不行，修改【文本】成可以直接写入 .py文件的形式，然后直接输出它（**不要附加任何不符合Python语法的内容**）
            """.format(text=response.content)
        system_message = {
            "role": "system",
            "content": python_code_system_prompt,
        }
        response = self.llm.invoke([system_message])

        return {"messages": [response]}

    @staticmethod
    def sanitize_input(query: str) -> str:
        query = re.sub(r"^(\s|`)*(?i:python)?\s*", "", query)
        query = re.sub(r"(\s|`)*$", "", query)
        return query

    def check_python_code(self,state: MessagesState) -> Command[Literal["generate_python_code", "run_python_code"]]:
        messages = state["messages"]
        code = messages[-1].content
        code = CodeCalculationAgent.sanitize_input(code)
        # 保存到 文件
        with open(self.code_file, "w", encoding="utf-8") as f:
            f.write(code)

        valida_imports = extract_imports(self.code_file, self.import_file)
        success, message = run_import_check(self.import_file)

        if not success:
            goto = "generate_python_code"
            response = AIMessage(
                f"The module does not exist. Use another module or install the module first before importing and using it.details: {message}")  # 格式化结果消息
            return Command(
                # this is the state update
                update={"messages": [response]},
                # this is a replacement for an edge
                goto=goto,
            )

        # check_result = run_bandit_cmd(r'agent_generate_code/my_code.py', output_format='json')
        check_result = run_bandit_cmd(self.code_file, output_format='json')

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
        response = self.llm.invoke([system_message])


        is_ok = "ok" in response.content

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

    def run_python_code(self,state: MessagesState) -> Command[Literal["generate_python_code", "check_output_val"]]:
        messages = state["messages"]
        code = messages[-1].content
        run_result = None
        is_ok = True
        try:
            result = subprocess.run(
                ["python", self.code_file],
                capture_output=True,
                text=True,
                encoding="utf-8",
                # 注意：这里不设置check=True，手动处理返回码
            )
            # 手动检查返回码
            if result.returncode == 0:
                run_result = result.stdout
            else:
                is_ok = False
                run_result = result.stderr
        except Exception as e:
            is_ok = False
            run_result = e

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

    @staticmethod
    def remove_thinks(text):
        # 匹配 <think> 和 </think> 之间的所有内容（包括标签）
        # .*? 表示非贪婪匹配，确保只匹配到最近的 </think>
        return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

    def check_output_val(self,state: MessagesState) -> Command[Literal["generate_python_code", END]]:
        messages = state["messages"]
        check_result_val_isValid_system_prompt = """
        【问题】：{question}
        【答案】：{ans}
    
        请你担任结果校验者，判断答案是否符合问题预期，并按照以下输出规则（**必须生成判断结果,符合就输出ok**）：
           - 符合预期时，仅输出：ok
           - 不符合预期时，仅输出具体原因
    
        注：如果当前任务属于计算任务，只需判断答案是否为数字，无需检验是否正确
    
        示例：
        【问题】：8*6？
        【答案】：48
    
        output:
        ok
        """.format(ans=messages[-1].content, question=messages[0].content)
        system_message = {
            "role": "system",
            "content": check_result_val_isValid_system_prompt,
        }
        # 调用模型检查
        response = self.llm.invoke([system_message] + state["messages"])

        cleaned_content = CodeCalculationAgent.remove_thinks(response.content)
        is_ok = ("ok" in cleaned_content) or ("null" in cleaned_content) or (cleaned_content.isspace() or cleaned_content == "")

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

    def get_agent(self):
        # 构建状态图
        builder = StateGraph(MessagesState)  # 以消息状态作为图的核心状态

        # 添加节点（每个节点对应一个处理步骤）
        builder.add_node(self.generate_python_code)
        builder.add_node(self.check_python_code)
        builder.add_node(self.run_python_code)
        builder.add_node(self.check_output_val)

        # 定义节点间的边
        builder.add_edge(START, "generate_python_code")
        builder.add_edge("generate_python_code", "check_python_code")

        # 编译图为可运行的代理
        agent = builder.compile()
        return agent

    @staticmethod
    def remove_code_run_prefix(s):
        prefix = "Code run result: "
        if s.startswith(prefix):
            return s[len(prefix):].lstrip()  # 使用 lstrip() 移除剩余的前导空白字符
        return s  # 如果字符串不以该前缀开头，则原样返回

    def run_agent(self, problem):
        agent = self.get_agent()

        last_message = None  # 初始化最后一个消息变量
        for step in agent.stream(
                {"messages": [{"role": "user", "content": problem}]},
                stream_mode="values",
        ):
            last_message = step["messages"][-1]  # 更新最后一个消息
            # 如果你不需要打印中间步骤，可以移除下面这行
            last_message.pretty_print()

        return CodeCalculationAgent.remove_code_run_prefix(last_message.content)  # 返回最后一个消息

@tool
def code_calculation_tool(problem:str):
    """
    传入需要计算的任务{problem}，通过调用python代码来解决。最后返回计算结果。
    :param problem: 自然语言描述
    """
    return CodeCalculationAgent().run_agent(problem)


common_tools = COMMON_TOOLS

class Calculation_agent(BaseToolAgent):

    def get_tools(self) -> List[Callable]:
        tools=common_tools+[code_calculation_tool,generate_reusable_functions_tool]
        return tools

    def call_tools(self, state: MessagesState):
        system_prompt = """
            1. 如果现有的工具能解决该问题，就直接调用现有工具解决；
            2. 没有现有工具就调用@tool code_calculation_tool通过写代码来解决;
            3. 没有现有工具,将问题抽象成更泛用的函数描述，调用@tool generate_reusable_functions_tool生成可复用的函数将其保存到工具库中
            
            :示例1:
                Human:计算59*59
                AI:tools中存在@tool multiply(a: float, b: float)，直接调用multiply计算，并告知用户结果
            :示例2:
                Human:计算59的66次方
                AI:tools中不存在tool能直接解决，调用@tool code_calculation_tool现写代码解决；并且抽象该问题为工具描述【计算一个数的n次方】，调用@tool generate_reusable_functions_tool生成可复用的函数将其保存到工具库中;最后将计算结果告知用户
            :return：
                最后只需告知用户计算结果，不需要多余表述。    
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
def calculation_tool(problem:str):
    """
    传入需要计算的任务{problem}，返回计算结果。
    :param problem: 自然语言描述
    """
    return Calculation_agent().run_agent(problem)

if __name__ == "__main__":
    print(Calculation_agent().run_agent("85*8*45*6?"))
    pass
