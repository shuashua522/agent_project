import copy
from typing import List, Callable, Annotated

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64

from langchain_core.tools import StructuredTool, tool
from langgraph.graph import MessagesState

from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm



class PrivacyHandler:
    def __init__(self):
        # self.key=self.generate_key()
        self.key=b'\x8dt\xa1\xafN\x11\xa1)>\xc4\x97zK1\xa5o'

    def encodeEntities(self,entities:list):
        result=[]
        for entity in entities:
            result.append(self.encodeEntity(entity))
        return result

    def decodeEntities(self,entities:list):
        result=[]
        for entity in entities:
            result.append(self.decodeEntity(entity))
        return result

    def encodeEntity(self, entity:dict):
        copied_entity = copy.deepcopy(entity)
        encode_key = {'context', 'entity_id', 'last_changed', 'last_updated', 'state', 'last_reported'}
        for key in copied_entity:
            # 若key在需加密的集合中，且对应值存在（非None）
            if key in encode_key and copied_entity[key] is not None:
                if(key=="context"):
                    for val in copied_entity[key]:
                        copied_entity[key][val]=self.encode(str(copied_entity[key][val]))
                elif(key=="entity_id"):
                    copied_entity[key]=self.encodeEntityId(copied_entity[key])
                # elif(key=="state"):
                #     encode_val=self.encode(str(copied_entity[key]))
                #     state_brief_description=self.generate_state_brief_description(entity)
                #     copied_entity[key] = f"{encode_val}({state_brief_description})"
                else:
                    encode_value = self.encode(str(copied_entity[key]))
                    copied_entity[key] = encode_value
        return copied_entity

    def decodeEntity(self,entity:dict):
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

    def generate_state_brief_description(self,entity):
        from agent_project.agentcore.commons.utils import get_llm
        # return "仅测试，未调用llm"
        llm=get_llm()
        response=llm.invoke("用一句话简练描述state的值，但绝对不能透露其值目前的状态")
        return response.content

    def encodeEntityId(self,entityId:str):
        parts = entityId.split('.', 1)
        if len(parts) != 2:
            raise ValueError("实体ID传入错误")
        domain_part, id_part = parts

        id_part = self.encode(id_part)
        return f"{domain_part}.{id_part}"

    def decodeEntityId(self,entityId:str):
        parts = entityId.split('.', 1)
        if len(parts) != 2:
            raise ValueError("实体ID传入错误")
        domain_part, id_part = parts

        id_part = self.decode(id_part)
        return f"{domain_part}.{id_part}"
    def generate_key(self,key_size=128):
        if key_size not in [128, 192, 256]:
            raise ValueError("密钥长度必须是128、192或256位")
        return os.urandom(key_size // 8)


    def encode(self,plaintext):
        iv = os.urandom(16)
        pad_length = 16 - (len(plaintext.encode('utf-8')) % 16)
        padded_plaintext = plaintext.encode('utf-8') + bytes([pad_length]) * pad_length
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
        return f"{base64.b64encode(iv).decode('utf-8')}:{base64.b64encode(ciphertext).decode('utf-8')}"


    def decode(self,encrypted_text):
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
        tools=[StructuredTool.from_function(PRIVACYHANDLER.decode)]
        return tools

    def call_tools(self, state: MessagesState):
        system_prompt = """
                    你是一名数据解密助手，你需要：
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
    # 1. 生成密钥（实际应用中需妥善保存，解密必须用相同密钥）
    aes_key = handler.key  # 16字节密钥
    print(handler.key)
    print(f"密钥（Base64）：{base64.b64encode(aes_key).decode('utf-8')}\n")

    # 2. 原始文本
    original_text = "这是一段需要加密的隐私文本：Hello, World! 12345"
    print(f"原始文本：{original_text}")

    # 3. 加密
    encrypted = handler.encode(original_text)
    print(f"加密后：{encrypted}\n")

    # 4. 解密
    decrypted = handler.decode(encrypted)
    print(f"解密后：{decrypted}")
    print(f"解密是否正确：{decrypted == original_text}")  # 验证一致性

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
    body="""
    {"entity_id": "nB/MRO8IqOyD9Kj8t9A3kw==:5sWFd4t1UNtxvhX2LYYaqOZ6aVIKfXw7LiBwXmE/d38n30HHZColHIGWTZPpQlo6", "brightness_pct": {n+4XiEGjo3K4qp1+WdooLw==:E034U68+xYq6U47e5i/isA==}*5-4}
    """
    print(RequestBodyDecodeAgent().run_agent(body))

# 示例运行
if __name__ == "__main__":
    # testClass_PrivacyHandler()
    # testAgent_ResultDecodeAgent()
    # testAgent_RequestBodyDecodeAgent()
    pass