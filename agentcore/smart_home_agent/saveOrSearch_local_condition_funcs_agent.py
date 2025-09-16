import json
from pathlib import Path
from typing import List, Callable, Annotated

from langchain_core.tools import tool
from langgraph.graph import MessagesState

from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm


@tool
def save_func_code_to_file(func_code: str):
    """
    将python函数字符串{func_code}保存到函数库中

    参数:
        func_code: 包含函数定义的字符串

    注意：只要没有抛出异常，即可视为成功保存到函数库中
    """
    # 创建一个字典来存储动态执行的代码中的对象
    global_namespace = {}
    # 执行函数代码字符串
    exec(func_code, global_namespace)

    # 获取当前文件所在的目录路径
    current_dir = Path(__file__).resolve().parent
    # 构建目标目录路径：当前目录/generate_conditional_code
    target_dir = current_dir / "generate_conditional_code"
    # 构建目标文件路径：目标目录/condtional_code.py
    target_file = target_dir / "condtional_code.py"

    try:
        # 创建目录（如果不存在），parents=True确保父目录存在，exist_ok=True避免目录已存在时报错
        target_dir.mkdir(parents=True, exist_ok=True)

        # 追加写入代码到文件（若文件不存在则自动创建）
        # 使用utf-8编码确保中文等特殊字符正常写入
        with open(target_file, "a", encoding="utf-8") as f:
            # 追加前先换行，避免代码粘连在同一行
            f.write("\n" + func_code + "\n")

    except Exception as e:
        # 抛出异常以便调用方处理
        raise Exception(f"保存函数代码失败: {str(e)}")

@tool
def load_funcs_from_file():
    """
    加载所有本地函数的函数名及其文档字符串说明的函数用途，返回json字符串.
    如果本地函数库没有，则不会返回函数字符串，可能返回None或{}或...
    """
    # 构建文件路径
    current_dir = Path(__file__).resolve().parent
    target_file = current_dir / "generate_conditional_code" / "condtional_code.py"

    try:
        if not target_file.exists():
            return json.dumps({})

        # 动态导入模块
        global_namespace = {}
        with open(target_file, "r", encoding="utf-8") as f:
            code = f.read()
            exec(code, global_namespace)

        # 收集函数信息
        functions_info = {}
        for name, obj in global_namespace.items():
            if callable(obj) and not name.startswith("__"):
                # 获取文档字符串，默认空字符串
                docstring = obj.__doc__ or ""
                # 清理文档字符串格式
                docstring = " ".join([line.strip() for line in docstring.splitlines() if line.strip()])
                functions_info[name] = docstring

        return json.dumps(functions_info, ensure_ascii=False, indent=2)

    except Exception as e:
        raise Exception(f"加载函数信息失败: {str(e)}")

@tool
def load_func_code_from_file(func_name: str):
    """
    加载本地函数库中函数名为{func_name}的函数，返回其对应的函数字符串;
    """
    # 构建文件路径
    current_dir = Path(__file__).resolve().parent
    target_file = current_dir / "generate_conditional_code" / "condtional_code.py"

    try:
        if not target_file.exists():
            raise Exception("函数库文件不存在")

        # 读取文件内容
        with open(target_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 查找函数定义
        func_code = []
        in_function = False
        func_def_prefixes = [f"def {func_name}(", f"async def {func_name}("]

        for line in lines:
            # 检查是否是目标函数定义行
            if any(line.strip().startswith(prefix) for prefix in func_def_prefixes):
                in_function = True
                func_code.append(line)
            # 收集函数内部代码
            elif in_function:
                # 检查缩进判断函数结束
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith(('#', '@')) and not line.startswith('    '):
                    in_function = False
                    break
                func_code.append(line)

        if not func_code:
            raise Exception(f"未找到函数 {func_name}")

        # 合并函数代码并清理空行
        return ''.join(func_code).strip() + '\n'

    except Exception as e:
        raise Exception(f"加载函数代码失败: {str(e)}")

class Search_local_contionalCode_agent(BaseToolAgent):
    def get_tools(self) -> List[Callable]:
        tools=[load_funcs_from_file,load_func_code_from_file]
        return tools

    def call_tools(self, state: MessagesState):
        """
               让LLM根据功能描述，生成一个函数代码，最后转化为工具以复用
               """
        # llm = get_llm().bind_tools(self.get_tools(), tool_choice="save_function_to_commons")
        llm = get_llm().bind_tools(self.get_tools())
        # 提示词：强制LLM生成规范的BaseTool子类，包含必要属性和方法
        prompt = f"""
                   基于用户的问题描述，检查本地函数库中是否存在对应的实现；如果存在，返回其对应的函数字符串.
                   工具调用参考：
                   1. 先调用@tool load_funcs_from_file查看本地函数库中的所有函数名及其对应的描述
                        - 如果有描述与用户需求一致，调用工具@tool load_func_code_from_file获取其函数源码字符串，然后return 函数源码字符串 
                        - 如果没有描述与用户需求一致，直接return "本地函数库没有对应的函数实现"
       """
        system_message = {
            "role": "system",
            "content": prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        return {"messages": [response]}

@tool
def search_local_contionalCode_tool(condition_statement: Annotated[str, "需要检查的条件，自然语言描述;比如卧室的光照是否充足"]):
    """
    检查本地函数库中是否存在对应的python函数，用于检查条件{condition_statement}是否已满足
    :return: python函数字符串
   基于用户的问题描述，检查本地函数库中是否存在对应的实现；如果存在，返回其对应的函数字符串
   """
    return Search_local_contionalCode_agent().run_agent(condition_statement)


# Search_local_contionalCode_agent().run_agent("门窗是否打开")