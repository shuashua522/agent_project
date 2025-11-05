# 1. 导入需要的库
from dataclasses import dataclass
from typing_extensions import TypedDict
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool, ToolRuntime
from langgraph.store.memory import InMemoryStore  # 测试用，生产换DB存储

from agent_project.agentcore.commons.utils import get_llm


# 2. 定义「上下文」：用来传递用户ID（定位谁的记忆）
@dataclass
class UserContext:
    user_id: str  # 每个用户唯一ID，比如从登录信息里获取


# 3. 定义「记忆数据格式」：规范要保存的用户偏好结构（让LLM知道该要什么信息）
class CoffeePreference(TypedDict):
    drink_type: str  # 咖啡类型，比如“拿铁”“美式”
    sugar: str       # 糖量，比如“不要糖”“少糖”
    milk: str = "全脂奶"  # 可选参数，默认全脂奶


# 4. 初始化「长期记忆存储」（测试用InMemoryStore，生产换PostgreSQL等）
memory_store = InMemoryStore()


# 5. 定义工具1：保存用户的咖啡偏好（写入记忆）
@tool
def save_coffee_preference(
    preference: CoffeePreference,  # 接收用户偏好数据
    runtime: ToolRuntime[UserContext]  # 用来获取当前用户ID和存储
) -> str:
    """保存用户的咖啡偏好到记忆中，比如喜欢的咖啡类型、糖量"""
    # ① 从上下文里拿到当前用户的ID（知道要存哪个用户的记忆）
    current_user_id = runtime.context.user_id
    # ② 把偏好写入存储：命名空间用("user_coffee", current_user_id)，确保每个用户的记忆独立
    memory_store.put(
        namespace=("user_coffee", current_user_id),  # 命名空间：归类为“用户咖啡偏好+用户ID”
        key="preference",  # 键：给这条记忆起个名字，方便后续读取
        value=preference   # 值：用户的具体偏好（JSON格式）
    )
    return f"已记住你的咖啡偏好：{preference}"


# 6. 定义工具2：获取用户的咖啡偏好（读取记忆）
@tool
def get_coffee_preference(
    runtime: ToolRuntime[UserContext]  # 用来获取当前用户ID和存储
) -> str:
    """从记忆中获取用户之前保存的咖啡偏好"""
    # ① 拿到当前用户ID
    current_user_id = runtime.context.user_id
    # ② 从存储中读取该用户的咖啡偏好
    saved_preference = memory_store.get(
        namespace=("user_coffee", current_user_id),  # 跟写入时的命名空间一致
        key="preference"  # 跟写入时的键一致
    )
    # ③ 判断是否有保存的偏好，没有就返回提示
    if saved_preference:
        return f"你的咖啡偏好是：{saved_preference.value}"
    else:
        return "还没记录你的咖啡偏好，你喜欢喝什么咖啡呀？"


# 7. 创建智能体（把模型、工具、记忆存储关联起来）
llm = get_llm()

agent = create_react_agent(
    model=llm,
    tools=[save_coffee_preference, get_coffee_preference],  # 把两个工具传给智能体
    store=memory_store,  # 把记忆存储传给智能体，让工具能访问
    context_schema=UserContext  # 告诉智能体要用UserContext传递用户ID
)


# 8. 测试交互（模拟用户两次对话）
print("=== 第一次对话：用户告诉偏好（写入记忆）===")
# 调用智能体，传入用户消息和当前用户ID（这里假设用户ID是"user_001"）
result1 = agent.invoke(
    {"messages": [{"role": "user", "content": "我喜欢喝拿铁，不要糖，用脱脂奶"}]},
    context=UserContext(user_id="user_001")  # 关键：指定要记录哪个用户的记忆
)
print("机器人回复：", result1["messages"][-1]["content"])  # 打印机器人回复


print("\n=== 第二次对话：用户问偏好（读取记忆）===")
# 再次调用智能体，同样传入用户ID，机器人会读取之前保存的记忆
result2 = agent.invoke(
    {"messages": [{"role": "user", "content": "我之前说过喜欢什么咖啡来着？"}]},
    context=UserContext(user_id="user_001")  # 还是同一个用户ID，才能读到之前的记忆
)
print("机器人回复：", result2["messages"][-1]["content"])  # 打印机器人回复