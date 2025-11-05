# 1. 导入低版本所需库
from dataclasses import dataclass
from typing_extensions import TypedDict
from langchain.agents import create_react_agent, AgentExecutor  # 低版本用create_react_agent
from langchain.tools import Tool  # 低版本需要用Tool类包装工具
from langchain import LLMChain
from langchain.prompts import PromptTemplate
from langgraph.store.memory import InMemoryStore

from agent_project.agentcore.commons.utils import get_llm


# 2. 定义用户上下文（传递user_id）
@dataclass
class UserContext:
    user_id: str  # 用户唯一标识


# 3. 定义咖啡偏好的数据格式
class CoffeePreference(TypedDict):
    drink_type: str  # 咖啡类型
    sugar: str       # 糖量
    milk: str = "全脂奶"  # 奶类型（默认全脂）


# 4. 初始化长期记忆存储（和之前一样）
memory_store = InMemoryStore()


# 5. 定义工具函数（低版本：手动接收store和user_id，不依赖ToolRuntime）
def save_coffee_preference(preference_str: str, user_id: str, store: InMemoryStore) -> str:
    """保存用户的咖啡偏好到记忆中。输入格式应为字典字符串，例如：{'drink_type': '拿铁', 'sugar': '不要糖'}"""
    import json
    try:
        # 解析用户输入的字符串为字典（低版本需要手动处理格式）
        preference = json.loads(preference_str)
        # 写入存储（命名空间和键与之前一致）
        store.put(
            namespace=("user_coffee", user_id),
            key="preference",
            value=preference
        )
        return f"已记住你的咖啡偏好：{preference}"
    except Exception as e:
        return f"保存失败，请检查格式：{str(e)}"


def get_coffee_preference(user_id: str, store: InMemoryStore) -> str:
    """从记忆中获取用户的咖啡偏好"""
    saved_preference = store.get(
        namespace=("user_coffee", user_id),
        key="preference"
    )
    if saved_preference:
        return f"你的咖啡偏好是：{saved_preference.value}"
    else:
        return "还没记录你的咖啡偏好，你喜欢喝什么咖啡呀？"


# 6. 包装工具（低版本需要用Tool类显式定义，绑定参数）
def get_tools(user_id: str, store: InMemoryStore):
    # 工具1：保存偏好（通过partial固定user_id和store）
    from functools import partial
    save_tool_func = partial(save_coffee_preference, user_id=user_id, store=store)
    save_tool = Tool(
        name="SaveCoffeePreference",
        func=save_tool_func,
        description="保存用户的咖啡偏好，输入必须是字典字符串（例如：{'drink_type': '拿铁', 'sugar': '不要糖'}）"
    )

    # 工具2：获取偏好（同样固定user_id和store）
    get_tool_func = partial(get_coffee_preference, user_id=user_id, store=store)
    get_tool = Tool(
        name="GetCoffeePreference",
        func=get_tool_func,
        description="获取用户之前保存的咖啡偏好，不需要输入参数"
    )
    return [save_tool, get_tool]


# 7. 创建智能体（低版本用create_react_agent + AgentExecutor）
def create_low_version_agent(llm, tools):
    # 定义智能体提示词（低版本需要手动指定）
    prompt = PromptTemplate(
        input_variables=["input", "agent_scratchpad", "tools"],
        template="""你是一个能记住用户咖啡偏好的助手。
可用工具：{tools}
使用工具的格式：思考后用```包裹调用，例如```[{"name":"工具名","parameters":{"参数名":"值"}}]```
用户输入：{input}
思考过程：{agent_scratchpad}
"""
    )
    # 创建React智能体
    agent = create_react_agent(llm, tools, prompt)
    # 用AgentExecutor包装（低版本执行智能体的标准方式）
    return AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True  # 打印思考过程，方便调试
    )


# 8. 测试交互
if __name__ == "__main__":
    # 初始化LLM（用Claude，换成OpenAI也可以）
    llm = get_llm()

    # 模拟用户ID（实际场景从登录信息获取）
    user_context = UserContext(user_id="user_001")

    # 获取绑定当前用户的工具
    tools = get_tools(
        user_id=user_context.user_id,
        store=memory_store
    )

    # 创建智能体
    agent_executor = create_low_version_agent(llm, tools)

    # 第一次对话：保存偏好
    print("=== 第一次对话：保存偏好 ===")
    result1 = agent_executor.run("我喜欢喝拿铁，不要糖，用脱脂奶。请用工具保存我的偏好，格式为字典字符串")
    print("机器人回复：", result1)

    # 第二次对话：读取偏好
    print("\n=== 第二次对话：读取偏好 ===")
    result2 = agent_executor.run("我之前喜欢什么咖啡？用工具查一下")
    print("机器人回复：", result2)