import copy

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64



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


# 示例运行
if __name__ == "__main__":
    handler=PrivacyHandler();
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