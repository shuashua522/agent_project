import json

from langchain_core.output_parsers import PydanticOutputParser

from agent_project.agentcore.commons.utils import get_llm, extract_json_content
from pydantic import BaseModel, Field


class JsonResponse(BaseModel):
    response: str = Field(
        description="一段符合json格式的字符串"
    )
    explanation: str = Field(
        description="Return an explanation of the response to the user"
    )

decode_body="""{"a":5*3,"name":"4+5"}"""

format_instructions = PydanticOutputParser(
    pydantic_object=JsonResponse
).get_format_instructions()

system_prompt = f"""如果这段json中的内容涉及算术运算，那么你需要计算其中的数学运算！
        【request_body】：{decode_body}
        
        {format_instructions}
        """
system_message = {
    "role": "system",
    "content": system_prompt,
}
print(system_message)
response = get_llm().invoke([system_message])
print(response)
print(response.content)

body=extract_json_content(response.content)
result=json.loads(body[0])
print(result)

