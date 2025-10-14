import warnings

from langchain.chat_models import init_chat_model
from langgraph.graph import MessagesState

from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm
from agent_project.agentcore.config.global_config import MODEL, BASE_URL, API_KEY, PROXIES, PROVIDER
import agent_project.agentcore.config.global_config as global_config


from langchain_core.callbacks import BaseCallbackHandler, CallbackManager
from langchain.chat_models import init_chat_model
from typing import Any, Dict, List, Callable
from langchain_core.tools import tool

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

# 使用示例
callback = TokenTrackingCallback()
# llm = init_chat_model(
#     model="gpt-3.5-turbo",  # 可替换为其他模型（如 "claude-3-haiku-20240307"）
#     callback_manager=CallbackManager([callback]),
#     temperature=0
# )
global_config.TOKEN_TRACKING_CALLBACK=callback

@tool
def calc_nums(a,b):
    """
    计算任意两个数之和
    :param a: 一个数字
    :param b: 另一个数字
    :return: 两个数的和
    """
    return a+b
class testAgent(BaseToolAgent):

    def get_tools(self) -> List[Callable]:
        tools=[calc_nums]
        return tools

    def call_tools(self, state: MessagesState):
        system_prompt = """
                            通过调用给定的工具回答用户问题
                        """
        llm = get_llm().bind_tools(self.get_tools())
        system_message = {
            "role": "system",
            "content": system_prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        print(response.content)
        return {"messages": [response]}


testAgent().run_agent("1+1=? ")
# 打印结果
print(f"token usage list: {callback.token_usages}")
print(f"输入 token: {callback.total_prompt_tokens}")
print(f"输出 token: {callback.total_completion_tokens}")
print(f"总 token: {callback.total_tokens}")

# llm=get_llm([callback])
# # 调用模型
# response = llm.invoke("1+1=? 直接给出结果")
# print(response)
# # 打印结果
# print(f"token usage list: {callback.token_usages}")
# print(f"输入 token: {callback.total_prompt_tokens}")
# print(f"输出 token: {callback.total_completion_tokens}")
# print(f"总 token: {callback.total_tokens}")

