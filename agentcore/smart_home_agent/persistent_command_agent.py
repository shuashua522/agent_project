import uuid
from typing import Annotated, List, Callable

from langgraph.graph import MessagesState

from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm



from abc import abstractmethod
from langchain_core.tools import tool

from agent_project.agentcore.smart_home_agent.queueBased_scheduler import generateTaskToQueueTool
from agent_project.agentcore.smart_home_agent.saveOrSearch_local_condition_funcs_agent import \
    search_local_contionalCode_tool, save_func_code_to_file
from agent_project.agentcore.smart_home_agent.test_with_baselines.baselines_homeassitant.sage.smart.smartThings import \
    get_all_entity_id, get_states_by_entity_id


class GenerateConditionCode(BaseToolAgent):
    def get_tools(self):
        tools = [get_all_entity_id,
                 get_states_by_entity_id,
                 save_func_code_to_file,
                 ]
        return tools

    def call_tools(self, state: MessagesState):
        """
            :param condition:
            :return:
            """
        uuid_str = str(uuid.uuid4()).replace("-", "_")
        system_prompt = """

                    Please generate a parameterless Python function based on the user's needs. The function name is fixed as {func_name}, and the function is in the form of:
                    def {func_name}()-> bool:

                    The user's needs are generally to check whether the status of the device meets the conditions:
                    1. You need to determine which devices to check, and this step can be confirmed by calling @tool get_all_entity_id;
                    2. You need to generate code to check whether the corresponding device meets the conditions; if it does, return true. In this step, you can make conditional judgments based on the status returned by @tool get_states_by_entity_id; if you are unsure of what the returned status contains, you can first call @tool get_states_by_entity_id to check, with a maximum of one call per entity_id.

                    - You should not call get_all_entity_id in the generated code, because it is used for you to determine the entity_id of the device; after determining the entity_id, calling get_states_by_entity_id will allow you to obtain the required status information
                    - The tools provided to you can be called in the code like local functions. For example, to call @tool calculate_area in the code:
                    print(get_all_entity_id())

                    Requirements for generated code:
                    - Must correctly call the above tools, and the parameter types must match
                    - The code needs to have comments explaining the logic
                    - Handle possible exceptions (such as negative radius)
                    - Must add a docstring to explain the function's purpose

                    **After generating the code, call @tool save_func_code_to_file to save it to the local function library**
                    - As long as calling @tool save_func_code_to_file does not report an error, the saving is successful
                    - Do not repeatedly call @tool save_func_code_to_file,
                    - Once saved to the function library, the process should end; do not write code multiple times and then call @tool save_func_code_to_file,

                    Finally！！！！>>>Return format: Return only pure Python code！！！
                    """.format(func_name="func" + uuid_str)
        llm = get_llm().bind_tools(self.get_tools())
        system_message = {
            "role": "system",
            "content": system_prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        print(response.content)
        return {"messages": [response]}

@tool
def generateConditionCodeTool(condition_statement: Annotated[str, "Condition to be checked, described in natural language; for example, whether the light in the bedroom is sufficient"]):
    """
    Generate a Python function to check whether the condition {condition_statement} is met
    :return: Python function string
    """
    return GenerateConditionCode().run_agent(condition_statement)

class PersistentCommandAgent(BaseToolAgent):
    def get_tools(self) -> List[Callable]:
        tools=[generateConditionCodeTool,
               generateTaskToQueueTool,
               search_local_contionalCode_tool]
        return tools

    def call_tools(self, state: MessagesState):
        system_prompt = """
                    Call tools to achieve persistent monitoring of the user's instructions
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
def persistentCommandTool(task: Annotated[str, "Description of the task requiring persistent monitoring"])->str:
    """
        Can perform persistent monitoring based on the task description.
        :Example 1:
            task="When the network is disconnected, notify me":
        :Example 2:
            task="Every Sunday, report the usage of smart home devices this week":
        :Example 3:
            task="Every hour, read sensor data and store it in the database":
    """
    return PersistentCommandAgent().run_agent(task)

if __name__ == "__main__":
    # task="每隔一天，检查光照是否充足"
    # task="当门窗打开时，关闭空调"
    # task="当插座关闭时，邮件通知我"
    # PersistentCommandAgent().run_agent(task)
    # task="光照是否充足"
    # GenerateConditionCode().run_agent(task)
    pass