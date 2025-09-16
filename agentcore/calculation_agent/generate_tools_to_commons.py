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

from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm
from agent_project.agentcore.config.global_config import COMMON_TOOLS, get_context_logger
from pathlib import Path

logger = get_context_logger()

common_tools = COMMON_TOOLS

def save_func_code_to_file(func_code: str):
    """
    将函数代码字符串追加到当前文件所在目录下的generate_tool_func_code/tool_func_code.py中

    :param func_code: 要追加写的函数代码字符串
    :type func_code: str
    """
    # 获取当前文件所在的目录路径
    current_dir = Path(__file__).resolve().parent
    # 构建目标目录路径：当前目录/generate_tool_func_code
    target_dir = current_dir / "generate_tool_func_code"
    # 构建目标文件路径：目标目录/tool_func_code.py
    target_file = target_dir / "tool_func_code.py"

    try:
        # 创建目录（如果不存在），parents=True确保父目录存在，exist_ok=True避免目录已存在时报错
        target_dir.mkdir(parents=True, exist_ok=True)

        # 追加写入代码到文件（若文件不存在则自动创建）
        # 使用utf-8编码确保中文等特殊字符正常写入
        with open(target_file, "a", encoding="utf-8") as f:
            # 追加前先换行，避免代码粘连在同一行
            f.write("\n" + func_code + "\n")

        # print(f"函数代码已成功追加到: {target_file}")

    except Exception as e:
        print(f"保存函数代码失败: {str(e)}")

@tool
def save_function_to_commons(func_code: str, func_name: str) -> str:
    """
    将python函数字符串{func_code}保存到函数库中

    参数:
        func_code: 包含函数定义的字符串
        func_name: 要提取的函数名

    注意：只要没有抛出异常，即可视为成功保存到函数库中
    """
    # 创建一个字典来存储动态执行的代码中的对象
    global_namespace = {}

    # 执行函数代码字符串
    exec(func_code, global_namespace)

    # 从命名空间中获取函数
    if func_name in global_namespace:
        func = global_namespace[func_name]
        new_tool = StructuredTool.from_function(func=func)
        common_tools.append(new_tool)
        save_func_code_to_file(func_code)
        logger.info(f"common_tools目前状况：{common_tools}")
        return "已成功执行"
    else:
        raise ValueError(f"函数 {func_name} 未在提供的代码中定义")

class GenerateToolCodeAgent(BaseToolAgent):
    def get_tools(self):
        tools=[save_function_to_commons]
        return tools

    def call_tools(self, state: MessagesState):
        """
        让LLM根据功能描述，生成一个函数代码，最后转化为工具以复用
        """
        # llm = get_llm().bind_tools(self.get_tools(), tool_choice="save_function_to_commons")
        llm = get_llm().bind_tools(self.get_tools())
        # 提示词：强制LLM生成规范的BaseTool子类，包含必要属性和方法
        prompt = f"""
            基于用户的问题，抽象出可复用的函数，并将其保存到函数库中。
            **只要成功将函数保存到库中，即可结束。**
            
            注意！！：避免使用*args，改用显式的列表参数

            假设需满足功能求两个数相加，save_function_to_commons，参数func_name="add",func_code=
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
            "content": prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        return {"messages": [response]}

@tool
def generate_reusable_functions_tool(problem:str):
    """
    传入{problem}，根据描述生成函数代码并保存到本地工具库中;
    :param problem: 自然语言描述；函数的功能应该是可复用的;problem中应该包括函数名和对应的功能描述，函数名不应与现有工具名重复。
    """
    return GenerateToolCodeAgent().run_agent(problem)

if __name__ == "__main__":
    # GenerateToolCodeAgent().run_agent("三个数相加")
    # func1_code = """def func1():
    #     \"\"\"这是func1的文档字符串，会被用作工具描述\"\"\"
    #     print("func1")
    # """
    #
    # func2_code = """def func1():
    #     \"\"\"这是更新后的func1文档字符串\"\"\"
    #     print("func2")
    # """
    # save_function(func1_code, "func1")
    # save_function(func2_code, "func1")
    # print(common_tools)

    # GenerateToolCodeAgent().run_agent("求两个数相乘")
    #
    # llm = get_llm()
    # print(common_tools)
    # llm_with_tools = llm.bind_tools(common_tools)
    # print(llm_with_tools.invoke("请计算 123 乘上 456 等于多少？"))
    pass