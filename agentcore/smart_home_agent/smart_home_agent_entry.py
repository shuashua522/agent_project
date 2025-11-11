from typing import List, Callable

from langchain_core.tools import tool, StructuredTool
from langgraph.graph import MessagesState

from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm, get_local_llm
from agent_project.agentcore.smart_home_agent.device_interaction_agent import deviceInteractionTool
from agent_project.agentcore.smart_home_agent.memory_preference_agent import memory_tool
from agent_project.agentcore.smart_home_agent.persistent_command_agent import persistentCommandTool
from agent_project.agentcore.smart_home_agent.privacy_handler import ResultDecodeAgent, replace_encoded_text


class SmartHomeAgent(BaseToolAgent):
    def get_tools(self) -> List[Callable]:
        tools=[deviceInteractionTool,
               memory_tool,
               persistentCommandTool]
        return tools

    def call_tools(self, state: MessagesState):
        # system_prompt = """
        #     你是一名智能家居助手，调用工具以满足用户需求。
        #     - 不要向用户提问
        #     - 需要注意的是由于智能家居中的一些数据已经进行隐私处理，数据会被加密。
        #     - 因此，如果调用工具后的结果包含加密文本，你需要保留可能会用到的加密数据，后续我会进一步处理的。
        #     - 除了加密数据，你不能使用@符号
        #     - 在不清楚有什么设备前，禁止随意计划、无中生有。
        #     - 调用持久化的工具只需说清楚当xx设备处于xx状态时，就做什么。不需要提供任何加密数据
        # """
        system_prompt = """
                    You are a smart home assistant, call tools to meet user needs.
                    - Do not ask users questions
                    - It should be noted that some data in the smart home has been privacy-processed and will be encrypted.
                    - Therefore, if the result after calling the tool contains encrypted text, you need to retain the encrypted data that may be used; I will further process it later.
                    - Except for encrypted data, you cannot use the @ symbol
                    - Before knowing which devices are available, it is forbidden to make arbitrary plans or fabricate non-existent things.
                    - When calling persistent tools, you only need to clearly state what to do when a certain device is in a certain state. No need to provide any encrypted data
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
def smart_home_agent_tool(problem:str):
    """
    传入需要执行的智能家居任务{problem}；本工具会根据{problem}描述的任务完成对应操作。
    :param problem: 自然语言描述
    """
    encode_str=SmartHomeAgent().run_agent(problem)
    decode_str=replace_encoded_text(encode_str)
    system_prompt= f"""整理下面文本，使其更易于给用户观看
        用户的提问：{problem}
        处理结果：{decode_str}"""
    system_message = {
        "role": "system",
        "content": system_prompt,
    }
    response = get_local_llm().invoke([system_message])
    return response.content

def privacy_home_agent(problem:str):
    encode_str = SmartHomeAgent().run_agent(problem)
    decode_str = replace_encoded_text(encode_str)
    system_prompt = f"""Answer the user's question based on the reference information
                【Question】：{problem}
                【Reference Information】：{decode_str}"""
    system_message = {
        "role": "system",
        "content": system_prompt,
    }
    response = get_local_llm().invoke([system_message])
    import agent_project.agentcore.config.global_config as global_config
    logger = global_config.GLOBAL_AGENT_DETAILED_LOGGER
    if logger != None:
        logger.info("整理文本结果:\n"+response.content)
    return response.content
if __name__ == "__main__":
    encode_str = SmartHomeAgent().run_agent("有几个设备")
    decode_str=replace_encoded_text(encode_str)
    print(decode_str)
    # SmartHomeAgent().run_agent("每隔一天，检查光照是否充足")
    pass