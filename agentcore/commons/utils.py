import configparser
import logging
import os
import re
import warnings
from pathlib import Path
from typing import Any, Dict

from langchain.chat_models import init_chat_model
from langchain_core.callbacks import BaseCallbackHandler, CallbackManager


# 获取当前文件的绝对路径
current_file_path = os.path.abspath(__file__)
# 定位所在目录
current_dir = os.path.dirname(current_file_path)


def get_llm():
    import agent_project.agentcore.config.global_config as global_config
    from agent_project.agentcore.config.global_config import MODEL, BASE_URL, API_KEY, PROXIES, PROVIDER
    provider=PROVIDER
    model = MODEL
    base_url = BASE_URL
    api_key = API_KEY

    callbackHandler = global_config.TOKEN_TRACKING_CALLBACK;
    llm = None
    if (provider == "openai"):
        proxies = PROXIES
        import httpx
        httpx_client = httpx.Client()
        httpx_client.proxies = proxies
        if(callbackHandler):
            llm = init_chat_model(
                model=model,
                model_provider="openai",
                api_key=api_key,
                base_url=base_url,
                temperature=0,
                http_client=httpx_client,
                callback_manager=CallbackManager([callbackHandler]),
            )
        else:
            llm = init_chat_model(
                model=model,
                model_provider="openai",
                api_key=api_key,
                base_url=base_url,
                temperature=0,
                http_client=httpx_client
            )
    else:
        if(callbackHandler):
            llm = init_chat_model(
                model=model,
                model_provider="openai",
                api_key=api_key,
                base_url=base_url,
                temperature=0,
                callback_manager=CallbackManager([callbackHandler]),
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

def get_local_llm():
    model = "qwen2.5:0.5b"
    api_key = "ollama"
    base_url = "http://localhost:11434/v1"
    llm = init_chat_model(
        model=model,
        model_provider="openai",
        api_key=api_key,
        base_url=base_url,
        temperature=0,
    )
    return llm
def extract_json_content(text):
    """
    提取文本中被 ```json ``` 包裹的内容
    :param text: 原始文本
    :return: 提取到的JSON内容列表（可能包含多个匹配结果）
    """
    # 正则表达式模式：匹配 ```json 开头，``` 结尾，中间捕获所有内容（包括换行）
    # \s* 匹配标记前后的空白字符（空格、换行等）
    # .*? 非贪婪匹配，避免跨多个 ```json 块匹配
    # re.DOTALL 让 . 匹配换行符（支持多行内容）
    pattern = r'```json\s*(.*?)\s*```'
    matches = re.findall(pattern, text, re.DOTALL)
    return matches

def remove_thinks(text):
    # 匹配 <think> 和 </think> 之间的所有内容（包括标签）
    # .*? 表示非贪婪匹配，确保只匹配到最近的 </think>
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

def get_null_logger():
    null_logger = logging.getLogger("null_logger")
    null_logger.addHandler(logging.NullHandler())  # 添加空处理器
    null_logger.setLevel(logging.CRITICAL + 1)  # 级别设置为最高，屏蔽所有日志
    return null_logger

def get_context_logger(log_file=None, name=__name__):
    """配置能自动打印模块、类、函数信息的日志器"""
    # 处理默认日志文件路径
    if log_file is None:
        # 这里使用最新的 config_dir 值
        log_file = os.path.join(current_dir, 'agent_call.log')
    # 确保日志目录存在
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 格式化字符串：包含模块、函数、行号等信息
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s'
    )

    # 创建处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    # console_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    # console_handler.setFormatter(formatter)

    # 配置日志器
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    # logger.addHandler(console_handler)

    return logger

class TokenTrackingCallback(BaseCallbackHandler):
    def __init__(self):
        # 初始化总 token 计数器
        self.total_prompt_tokens = 0  # 累计输入 token
        self.total_completion_tokens = 0  # 累计输出 token
        self.total_tokens = 0  # 累计总 token
        self.token_usages=[]

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """
        LLM 调用结束时触发：提取 usage_metadata 并累加
        response: LLM 的响应对象，包含 usage_metadata 属性
        """
        # 检查响应是否包含 usage_metadata（避免模型不支持导致报错）
        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output['token_usage']
            self.token_usages.append(usage)
            # 累加输入 token（优先取 usage 中的 prompt_tokens，无则跳过）
            self.total_prompt_tokens += usage.get("prompt_tokens", 0)
            # 累加输出 token（优先取 usage 中的 completion_tokens，无则跳过）
            self.total_completion_tokens += usage.get("completion_tokens", 0)
            # 累加总 token（若有直接返回的 total_tokens 则用，否则手动计算）
            self.total_tokens += usage.get("total_tokens",
                                           self.total_prompt_tokens + self.total_completion_tokens)
        else:
            warnings.warn("当前 LLM 响应未包含 usage_metadata，无法统计 token 消耗")

    def get_agent_total_usage(self) -> Dict[str, int]:
        """返回 Agent 执行全程的 token 总消耗"""
        return {
            "累计输入 token": self.total_prompt_tokens,
            "累计输出 token": self.total_completion_tokens,
            "累计总 token": self.total_tokens
        }

if __name__ == "__main__":
    # print(get_llm().invoke("1+1=？"))
    pass