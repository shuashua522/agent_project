from typing import List, Callable

from langgraph.graph import MessagesState

from agent_project.agentcore.calculation_agent.calculation_agent_entry import calculation_tool
from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm
from agent_project.agentcore.smart_home_agent.smart_home_agent_entry import smart_home_agent_tool


class Agent_entry(BaseToolAgent):
    def get_tools(self) -> List[Callable]:
        tools=[smart_home_agent_tool,calculation_tool]
        return tools

    def call_tools(self, state: MessagesState):
        system_prompt = """
        调用恰当的工具以满足用户的需求
        """
        llm = get_llm().bind_tools(self.get_tools())
        system_message = {
            "role": "system",
            "content": system_prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        print(response.content)
        return {"messages": [response]}

if __name__ == "__main__":
    # print(Agent_entry().run_agent("目前网络状况"))
    print(Agent_entry().run_agent("5!=?"))