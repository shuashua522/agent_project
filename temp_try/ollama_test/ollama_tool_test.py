from agent_project.agentcore.commons.utils import get_llm
from agent_project.agentcore.smart_home_agent.device_interaction_agent import get_all_entity_id

llm=get_llm()
print(llm)
llm.bind_tools([get_all_entity_id])
response=llm.invoke("现在有哪些智能家居设备？")
print(response)