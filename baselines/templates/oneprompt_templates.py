from typing import Dict
from langchain.pydantic_v1 import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain import PromptTemplate


class OnePromptResponse(BaseModel):
    # 包含所有已更改设备状态的 JSON 数据。若未被要求更改设备状态，则返回空字典
    diff: Dict = Field(
        description="A JSON of all of the changed device states. If you are not asked to change device states, return an empty dict."
    )
    output: str = Field(description="A natural language response to the user query.")

# 你是一款控制智能家居的人工智能。你会接收用户指令以及所有设备的状态（以 JSON 格式呈现），然后作为响应为设备分配设置。
oneprompt_template = """
You are an AI that controls a smart home. You receive a user command and the state
of all devices (in JSON) format, and then assign settings to devices in response.

user command: {command}
devices: {device_state}

{format_instructions}
"""

# input template to llm
oneprompt_prompt_template = PromptTemplate(
    template=oneprompt_template,
    input_variables=["command", "device_state"],
    partial_variables={
        "format_instructions": PydanticOutputParser(
            pydantic_object=OnePromptResponse
        ).get_format_instructions()
    },
)
