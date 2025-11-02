import copy
import json
import re
from typing import List, Callable, Annotated

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.tools import StructuredTool, tool
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm, extract_json_content, get_local_llm


def add_sign(text: str):
    return f"@{text}@"


def replace_encoded_text(text):
    from agent_project.agentcore.config.global_config import PRIVACYHANDLER
    """找出所有@xxx@格式的文本并替换为decode的返回值（仅对@中间的内容解码）"""
    # 正则表达式匹配@开头、@结尾，且中间不含@的内容
    pattern = r'@[^@]+@'
    # 对匹配到的内容（如@xx@）先去掉首尾的@，再传入decode函数
    return re.sub(pattern, lambda m: PRIVACYHANDLER.decode(m.group().strip('@')), text)


class PrivacyHandler:
    def __init__(self):
        # self.key=self.generate_key()
        self.key = b'\x8dt\xa1\xafN\x11\xa1)>\xc4\x97zK1\xa5o'

    def encodeEntities(self, entities: list):
        result = []
        for entity in entities:
            result.append(self.encodeEntity(entity))
        return result

    def decodeEntities(self, entities: list):
        result = []
        for entity in entities:
            result.append(self.decodeEntity(entity))
        return result

    def encodeEntity(self, entity: dict):
        copied_entity = copy.deepcopy(entity)
        encode_key = {'context', 'entity_id', 'last_changed', 'last_updated', 'state', 'last_reported'}
        for key in copied_entity:
            # 若key在需加密的集合中，且对应值存在（非None）
            if key in encode_key and copied_entity[key] is not None:
                if (key == "context"):
                    for val in copied_entity[key]:
                        copied_entity[key][val] = add_sign(self.encode(str(copied_entity[key][val])))
                elif (key == "entity_id"):
                    copied_entity[key] = self.encodeEntityId(copied_entity[key])
                # elif(key=="state"):
                #     encode_val=self.encode(str(copied_entity[key]))
                #     state_brief_description=self.generate_state_brief_description(entity)
                #     copied_entity[key] = f"{encode_val}({state_brief_description})"
                else:
                    encode_value = self.encode(str(copied_entity[key]))
                    copied_entity[key] = add_sign(encode_value)
        return copied_entity

    def decodeEntity(self, entity: dict):
        copied_entity = copy.deepcopy(entity)
        encode_key = {'context', 'entity_id', 'last_changed', 'last_updated', 'state', 'last_reported'}
        for key in copied_entity:
            # 若key在需加密的集合中，且对应值存在（非None）
            if key in encode_key and copied_entity[key] is not None:
                if (key == "context"):
                    for val in copied_entity[key]:
                        copied_entity[key][val] = self.decode(str(copied_entity[key][val]))
                elif (key == "entity_id"):
                    copied_entity[key] = self.decodeEntityId(copied_entity[key])
                # elif (key == "state"):
                #     encode_str=copied_entity[key]
                #     encode_val=encode_str[:encode_str.find('(')]
                #     copied_entity[key] = self.decode(encode_val)
                else:
                    decode_value = self.decode(str(copied_entity[key]))
                    copied_entity[key] = decode_value
        return copied_entity

    def generate_state_brief_description(self, entity):
        from agent_project.agentcore.commons.utils import get_llm
        # return "仅测试，未调用llm"
        llm = get_llm()
        response = llm.invoke("用一句话简练描述state的值，但绝对不能透露其值目前的状态")
        return response.content

    def encodeEntityId(self, entityId: str):
        parts = entityId.split('.', 1)
        if len(parts) != 2:
            raise ValueError("实体ID传入错误")
        domain_part, id_part = parts

        id_part = add_sign(self.encode(id_part))
        return f"{domain_part}.{id_part}"

    def decodeEntityId(self, entityId: str):
        parts = entityId.split('.', 1)
        if len(parts) != 2:
            raise ValueError("实体ID传入错误")
        domain_part, id_part = parts

        id_part = self.decode(id_part)
        return f"{domain_part}.{id_part}"

    def generate_key(self, key_size=128):
        if key_size not in [128, 192, 256]:
            raise ValueError("密钥长度必须是128、192或256位")
        return os.urandom(key_size // 8)

    def encode(self, plaintext):
        iv = os.urandom(16)
        pad_length = 16 - (len(plaintext.encode('utf-8')) % 16)
        padded_plaintext = plaintext.encode('utf-8') + bytes([pad_length]) * pad_length
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
        return f"{base64.b64encode(iv).decode('utf-8')}:{base64.b64encode(ciphertext).decode('utf-8')}"

    def decode(self, encrypted_text):
        """
        对加密数据进行解码
        :param encrypted_text: 被加密的文本
        :return: 解密后的文本
        """
        try:
            iv_b64, ciphertext_b64 = encrypted_text.split(':')
        except ValueError:
            raise ValueError("加密文本格式错误，需符合 'IV_base64:密文_base64'")
        iv = base64.b64decode(iv_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        pad_length = padded_plaintext[-1]
        plaintext = padded_plaintext[:-pad_length].decode('utf-8')
        return plaintext

class JsonResponse(BaseModel):
    response: str = Field(
        description="一段符合json格式的字符串"
    )
    explanation: str = Field(
        description="Return an explanation of the response to the user"
    )
def jsonBodyDecodeAndCalc(body:str):
    # 解密
    body = replace_encoded_text(body)

    # 计算
    format_instructions = PydanticOutputParser(
        pydantic_object=JsonResponse
    ).get_format_instructions()

    system_prompt = f"""
    {body}
    如果上面这段json中的内容涉及算术运算，那么你需要手动计算其中的数学运算！否则，直接返回原本的json字符串
    - 直接返回一个json字符串
    - 最后返回的字符串的结构需要与原字符串保持一致
    - 不要写python代码
            
            
    {format_instructions}
            """
    system_message = {
        "role": "user",
        "content": system_prompt,
    }
    response = get_local_llm().invoke([system_message])

    jsonStrs = extract_json_content(response.content)
    # result = json.loads(body[0])
    return jsonStrs[0]

class RequestBodyDecodeAgent(BaseToolAgent):

    def get_tools(self) -> List[Callable]:
        from agent_project.agentcore.config.global_config import PRIVACYHANDLER
        tools = [StructuredTool.from_function(PRIVACYHANDLER.decode)]
        return tools

    def call_tools(self, state: MessagesState):
        system_prompt = """
                    你是一名数据解密助手，你需要对用户的json字符串进行解密：
                    1. 提取文本中的加密数据，调用工具对其解密
                    2. 如果加密数据前后涉及数学运算，那么数据解密后，你需要计算其中的数学运算！

                    需要注意的是：
                    - 只要解密工具没有报错或者抛出异常，那么返回的文本就是解密文本。比如解密后可能得到"unavailable"这样的文本，请不要认为这是解密工具调用失败！！

                    对所有加密文本解密后，并处理完毕其中涉及的算术运算后。你需要重新整理文本，返回一个json字符串！
                """
        llm = get_llm().bind_tools(self.get_tools())
        system_message = {
            "role": "system",
            "content": system_prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        print(response.content)
        return {"messages": [response]}


class ResultDecodeAgent(BaseToolAgent):

    def get_tools(self) -> List[Callable]:
        from agent_project.agentcore.config.global_config import PRIVACYHANDLER
        tools = [StructuredTool.from_function(PRIVACYHANDLER.decode)]
        return tools

    def call_tools(self, state: MessagesState):
        system_prompt = """
                    你是一名结果整理助手，你需要将文本整理成易于用户观看的
                    1. 提取文本中的加密数据
                    2. 调用工具对其解密
                    
                    需要注意的是：
                    - 只要解密工具没有报错或者抛出异常，那么返回的文本就是解密文本。比如解密后可能得到"unavailable"这样的文本，请不要认为这是解密工具调用失败！！
                    
                    对所有加密文本解密后，你需要重新整理文本，返回一个用户友好的文本！
                """
        llm = get_llm().bind_tools(self.get_tools())
        system_message = {
            "role": "system",
            "content": system_prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        print(response.content)
        return {"messages": [response]}


def testClass_PrivacyHandler():
    handler = PrivacyHandler();

    text = {
		"entity_id": "sensor.lumi_cn_551385025_mcn001_access_mode_p_2_5",
		"state": "",
		"attributes": {
			"friendly_name": "小米智能多模网关2  网关 网络变化状态string_fmt:{access-mode:{last:0,now:1],ip:{last:xx,now:xx},wifi-ssid:{last:xx,now:xx},time:12345678}}}"
		},
		"last_changed": "2025-10-09T02:17:40.351775+00:00",
		"last_reported": "2025-10-09T02:17:40.351775+00:00",
		"last_updated": "2025-10-09T02:17:40.351775+00:00",
		"context": {
			"id": "01K73C50QZ2YFQFCEWBERNMG3E",
			"parent_id": "null",
			"user_id": "null"
		}
	}

    decode_entity=handler.encodeEntity(text)
    print(f"decode_entity: {decode_entity}")
    clear_text=replace_encoded_text(str(decode_entity))
    print(f"clear_text: {clear_text}")


def testAgent_ResultDecodeAgent():
    encode_str = """
        以下是小米智能多模网关2的网络状况信息：
1. 接入方式：通过传感器`sensor.iiaBP/lw2PIoKcp4HgaPBg==:rvlB+HyVVVDqVNl690m62zrqydc4InM4LP13Sc2ttdAfN7rP6HdI8AQTHRRzEbh3`获取，状态为`lKenA1eSfYWW2M42ZpMpeg==:X6pQ9uY9erwFb/ar9npS2Q==`（注：可能为枚举值，需结合属性`options`判断，`options`为["有线", "2.4G 无线", "5G 无线"]）。
2. IP地址：通过传感器`sensor.2GVS9z4+T1W7SrpIAu84IQ==:R1Lj7hv/2a5mO6mClHoZcPrmA+SmH4TwRFPlZzpCsNtsaD6lSZRgO0WppNGXUTLJ`获取，状态为`UD1zOyiktIc2uqQqwJWbiQ==:cTA9x4MEjtWPDmbdG6gX+w==`。
3. WiFi网络名称(写权限无效)：通过传感器`sensor.evqqRty4VkMorDXHzq9s7Q==:Sg6idnHAkt0B/D8foGn4kQPatS5tGfoq0lRguE8GOx9r/i8sxi95tjNLRPc199I/`获取，状态为`oauVeyGF8NtnrzAeK/E5Iw==:HIhOYON0nW7IxsPUKWD80g==`。
4. 网络变化状态：通过传感器`sensor.nB/MRO8IqOyD9Kj8t9A3kw==:5sWFd4t1UNtxvhX2LYYaqOZ6aVIKfXw7LiBwXmE/d38n30HHZColHIGWTZPpQlo6`获取，状态为`Z91uJwX///nhsZ1RzYJ2fg==:73KwgXtROIABc7D25m8nUg==`，格式为`{access-mode:{last:0,now:1],ip:{last:xx,now:xx},wifi-ssid:{last:xx,now:xx},time:12345678}}`。

        """
    print(ResultDecodeAgent().run_agent(encode_str))


def testAgent_RequestBodyDecodeAgent():
    import json
    # print(PrivacyHandler().encode("50"))  # n+4XiEGjo3K4qp1+WdooLw==:E034U68+xYq6U47e5i/isA==
    # body = {
    #     "entity_id": "nB/MRO8IqOyD9Kj8t9A3kw==:5sWFd4t1UNtxvhX2LYYaqOZ6aVIKfXw7LiBwXmE/d38n30HHZColHIGWTZPpQlo6",
    #     "brightness": "{n+4XiEGjo3K4qp1+WdooLw==:E034U68+xYq6U47e5i/isA==}*5-4"
    # }
    # body = json.dumps(body)
    body = """
    {"entity_id": "nB/MRO8IqOyD9Kj8t9A3kw==:5sWFd4t1UNtxvhX2LYYaqOZ6aVIKfXw7LiBwXmE/d38n30HHZColHIGWTZPpQlo6", "brightness_pct": {n+4XiEGjo3K4qp1+WdooLw==:E034U68+xYq6U47e5i/isA==}*5-4}
    """
    print(RequestBodyDecodeAgent().run_agent(body))


# 示例运行
if __name__ == "__main__":
    # testClass_PrivacyHandler()
    # testAgent_ResultDecodeAgent()
    # testAgent_RequestBodyDecodeAgent()
    # print(replace_encoded_text("@OyXDhf1ROvIaW6/pBBquzA==:/Y7+KAElT9ySDIUHaHIOSrK7o+EhqHbUpkV3S+aceYs=@"))
    jsonBodyDecodeAndCalc('{"entity_id":"switch.@LfQOYZbHqKeNcVrw6u1FZw==:BzzlkkHWE02WNDNfJM0MBg3QO4QHKTDmUMk7LH+TZGY=@"}')
    pass

