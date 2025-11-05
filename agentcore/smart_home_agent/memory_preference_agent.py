from typing import List, Callable

from langgraph.graph import MessagesState
from langchain_core.tools import tool
from agent_project.agentcore.commons.base_agent import BaseToolAgent
from langgraph.store.memory import InMemoryStore

from agent_project.agentcore.commons.utils import get_llm

store = InMemoryStore()

@tool
def save_preference(preference_str: str) -> str:
    """添加用户的设备使用偏好到记忆中。输入格式应为字符串"""
    saved_preference = store.get(
        namespace=("user_preference", "_test"),
        key="preference"
    )
    existing_preference = saved_preference.value if saved_preference else ""

    combined_preference = f"{existing_preference};{preference_str}"  if existing_preference else preference_str

    store.put(
        namespace=("user_preference", "_test"),
        key="preference",
        value=combined_preference  # 存入拼接后的值
    )

    return f"已记住用户偏好：{preference_str}"

test_preferences_str = "把灯泡和音箱分组为 “氛围” 组；记住我喜欢客厅灯是 30% 亮度；台灯太亮了，亮度调到 20% 就行；哦，睡觉时，我不喜欢黑暗的环境，这会让我害怕；还是放周杰伦的歌吧，这是我最喜欢的；我接电话时，不要让设备发出声音；哦，我房间里有卫生间；看书时，我喜欢在客厅的沙发上看，因为累了，看看客厅的植物能让我心情放松；家里的插座没有我的明确指令不能关，上面连了我的服务器；客厅灯 3000k 是让我感觉最好；我喜欢关于动物和孩子的温暖治愈故事；网关的 wifi 目前连的是我的热点（dddiu）; 你知道什么场景最吓人吗？灯一闪一闪的，然后还有恐怖背景音；准备睡前我会玩会手机，这时灯设成渐灭，30 分钟后熄灭。; 周日，我一般天亮就起；暑假的时候，我晚上都会睡在客厅沙发，然后把窗户打开，这样睡得很香。; 我一般 11 点睡觉，7 点多起床；天气好的时候，窗户要打开通风哦"
@tool
def get_preference() -> str:
    """从记忆中获取用户的所有设备使用偏好"""
    import agent_project.agentcore.config.global_config as global_config
    if(global_config.ENABLE_MEMORY_FOR_TEST):
        store.put(
            namespace=("user_preference", "_test"),
            key="preference",
            value=test_preferences_str  # 存入拼接后的值
        )
    else:
        store.delete(
            namespace=("user_preference", "_test"),
            key="preference"
        )

    saved_preference = store.get(
        namespace=("user_preference", "_test"),
        key="preference"
    )
    if saved_preference:
        return f"偏好是：{saved_preference.value}"
    else:
        return "还没记录偏好"

class PreferenceAgent(BaseToolAgent):
    def __init__(self):
        pass
    def get_tools(self) -> List[Callable]:
        tools=[
                # save_preference,
               get_preference]
        return tools

    def call_tools(self, state: MessagesState):
        system_prompt = """
                   你需要从记忆库中找到与用户提问相关的偏好信息，并返回。
                   - 有可能记忆库中还没有用户相关的任何偏好信息，这时你需要告知用户暂时没有相关信息
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
def memory_tool(query:str):
    """
    从记忆中查找信息，有助于理解用户的模糊指令。
    也可能记忆中暂未存储用户相关信息，这时你需要自行决定最佳方案。
    """
    return PreferenceAgent().run_agent(query)

if __name__ == "__main__":
    store.put(
        namespace=("user_preference", "_test"),
        key="preference",
        value=test_preferences_str  # 存入拼接后的值
    )
    saved_preference = store.get(
        namespace=("user_preference", "_test"),
        key="preference"
    )
    print(saved_preference)
    store.delete(
        namespace=("user_preference", "_test"),
        key="preference"
    )
    saved_preference = store.get(
        namespace=("user_preference", "_test"),
        key="preference"
    )
    print(saved_preference)
    # store.put(
    #     namespace=("user_preference", "_test"),
    #     key="preference",
    #     value="我喜欢晴天;我喜欢下雨"  # 存入拼接后的值
    # )
    # print(PreferenceAgent().run_agent("我喜欢的食物"))
    # print(PreferenceAgent().run_agent("我喜欢的天气"))
    pass