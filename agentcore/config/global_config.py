import configparser
import importlib
import os
import logging
import sys
from pathlib import Path

from langchain_core.tools import StructuredTool

#======================llm
# 获取当前文件(global_config.py)的绝对路径
current_file_path = os.path.abspath(__file__)
# 定位到配置文件所在目录（与global_config.py同目录）
config_dir = os.path.dirname(current_file_path)
# 拼接配置文件的绝对路径
llm_config_file_path = os.path.join(config_dir, 'llm_config.ini')

# 创建配置解析器对象
llm_configparser = configparser.ConfigParser()
# 读取INI文件
llm_configparser.read(llm_config_file_path, encoding='utf-8')


# 设置LangSmith跟踪开关和API密钥
os.environ["LANGSMITH_TRACING"] = llm_configparser.get('LangSmith', 'langsmith_tracing')
os.environ["LANGSMITH_API_KEY"] = llm_configparser.get('LangSmith', 'langsmith_api_key')

PROVIDER = llm_configparser.get("base", 'selected_llm_provider')
MODEL = llm_configparser.get(PROVIDER, 'model')
BASE_URL = llm_configparser.get(PROVIDER, 'base_url')
API_KEY = llm_configparser.get(PROVIDER, 'api_key')

PROXIES = {
    'http': 'http://127.0.0.1:33210',  # HTTP 请求使用 33210 端口的 HTTP 代理
    'https': 'http://127.0.0.1:33210',  # HTTPS 请求使用 33210 端口的 HTTP 代理
}


#=====================================
# TODO 从本地文件加载可复用工具
COMMON_TOOLS=[]

def load_functions_to_tools():
    """
    加载指定文件中的所有函数，转换为StructuredTool并添加到COMMON_TOOLS中
    """
    try:
        # 获取当前文件所在目录的父目录
        current_dir = Path(__file__).resolve().parent
        parent_dir = current_dir.parent

        # 构建目标文件路径：父目录/calculation_agent/generate_tool_func_code/tool_func_code.py
        target_file = parent_dir / "calculation_agent" / "generate_tool_func_code" / "tool_func_code.py"

        # 检查文件是否存在
        if not target_file.exists():
            print(f"警告：目标文件不存在 - {target_file}")
            return

        # 动态导入模块
        module_name = "tool_func_module"  # 自定义模块名
        spec = importlib.util.spec_from_file_location(module_name, str(target_file))
        if spec is None:
            print(f"无法创建模块规范 - {target_file}")
            return

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module  # 将模块添加到sys.modules中

        # 执行模块，使函数定义生效
        if spec.loader is not None:
            spec.loader.exec_module(module)
        else:
            print(f"无法加载模块 - {target_file}")
            return

        # 收集模块中的所有函数
        func_dict = {}
        for name, obj in module.__dict__.items():
            # 排除内置函数和模块属性，只保留用户定义的函数
            if callable(obj) and not name.startswith("__"):
                func_dict[name] = obj

        # 将函数转换为StructuredTool并添加到COMMON_TOOLS
        for func_name, func in func_dict.items():
            try:
                tool = StructuredTool.from_function(func=func)
                COMMON_TOOLS.append(tool)
                print(f"已添加工具: {func_name}")
            except Exception as e:
                print(f"转换函数 {func_name} 为工具失败: {str(e)}")

    except Exception as e:
        print(f"加载函数到工具时发生错误: {str(e)}")
load_functions_to_tools()


#===================================== 日志
def get_context_logger(log_file=None, name=__name__):
    """配置能自动打印模块、类、函数信息的日志器"""
    # 处理默认日志文件路径
    if log_file is None:
        # 这里使用最新的 config_dir 值
        log_file = os.path.join(config_dir, 'agent_call.log')
    # 确保日志目录存在
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 格式化字符串：包含模块、函数、行号等信息
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s'
    )

    # 创建处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    console_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 配置日志器
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


#===================================== homeassitant 配置相关
HOMEASSITANT_AUTHORIZATION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkNzgwYTkyZGI2OTE0ZWExYTg2OGE1NmQ5ODcwOTU0OCIsImlhdCI6MTc1NjExODAwMywiZXhwIjoyMDcxNDc4MDAzfQ.DD600u9b5nGB0AwzVoIhonY2ACOs43Vp3IVvL5XN5aw"