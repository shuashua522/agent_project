import copy
import json

from typing import Dict, List, Callable, Any

from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from langgraph.graph import MessagesState

from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm, get_local_llm
from langchain_core.tools import tool

class PrivacyRunnableWrapper:
    """通用包装类，兼容LLM和bind_tools返回的Runnable对象"""
    def __init__(self, runnable: Runnable):
        self.runnable = runnable  # 被包装的Runnable（LLM/bind_tools后的对象）

    # 代理所有未显式定义的方法（保证原Runnable的方法正常调用）
    def __getattr__(self, name: str) -> Any:
        # 获取原Runnable的方法/属性
        attr = getattr(self.runnable, name)
        # 如果是可调用方法（如bind_tools、bind等），返回包装后的方法
        if callable(attr):
            def wrapped_method(*args, **kwargs):
                # 调用原方法，获取返回的新Runnable对象
                result = attr(*args, **kwargs)
                # 如果返回的是Runnable，自动包装成PrivacyRunnableWrapper
                if isinstance(result, Runnable):
                    return PrivacyRunnableWrapper(result)
                return result
            return wrapped_method
        return attr

    # 拦截invoke方法，插入encode/decode逻辑
    def invoke(self, input: Any, **kwargs) -> Any:
        input = copy.deepcopy(input)
        handler = PrivacyHandler()
        # 步骤1：调用encode加密输入（比如messages）
        encrypted_input = handler.encode(input)

        # 步骤2：调用原Runnable的invoke
        raw_response = self.runnable.invoke(encrypted_input, **kwargs)

        # 步骤3：调用decode解密输出
        # 步骤3：解密输出（兼容BaseMessage/字符串）
        if isinstance(raw_response, BaseMessage):
            raw_response.content = handler.decode(raw_response.content)
        elif isinstance(raw_response, str):
            raw_response = handler.decode(raw_response)

        # 返回解密后的结果
        return raw_response

def get_privacy_llm():
    llm = PrivacyRunnableWrapper(get_llm())
    return llm

class LLMWithPrivacyWrapper:
    def __init__(self, llm):
        self.llm = llm  # 包装第三方LLM实例

    # 代理所有未显式定义的方法（保证原LLM的其他方法正常使用）
    def __getattr__(self, name):
        # 除了invoke外，其他方法直接调用原LLM的方法
        return getattr(self.llm, name)

    # 重写invoke方法，插入encode/decode逻辑
    def invoke(self, input, **kwargs):
        input=copy.deepcopy(input)
        handler=PrivacyHandler()
        # 步骤1：调用encode加密输入（比如messages）
        encrypted_input = handler.encode(input)

        # 步骤2：调用原LLM的invoke方法
        raw_response = self.llm.invoke(encrypted_input, **kwargs)

        # 步骤3：调用decode解密输出
        raw_response.content = handler.decode(raw_response.content)

        # 返回解密后的结果
        return raw_response

@tool
def get_info():
    """
    获取设备信息
    """
    return """
    {
    "entity_id": "sensor.xiaomi_cn_blt_3_1ftnm7360c800_pir1_illumination_p_2_1005",
    "state": "0.0",
    "attributes": {
      "state_class": "measurement",
      "unit_of_measurement": "lx",
      "device_class": "illuminance",
      "friendly_name": "小米人体传感器2S  移动检测传感器 光照度"
    },
    "last_changed": "2025-11-04T06:56:10.188026+00:00",
    "last_reported": "2025-11-04T06:56:10.188026+00:00",
    "last_updated": "2025-11-04T06:56:10.188026+00:00",
    "context": {
      "id": "01K96TDMYC53SCFGSF9BYVJ6ZE",
      "parent_id": null,
      "user_id": null
    }
  },{
    "entity_id": "sensor.isa_cn_blt_3_1md0u6qht0k00_dw2hl_illumination_p_2_1",
    "state": "弱",
    "attributes": {
      "options": [
        "弱",
        "强"
      ],
      "device_class": "enum",
      "icon": "mdi:format-text",
      "friendly_name": "二楼卧室的门窗传感器  门窗传感器 光照度"
    },
    "last_changed": "2025-10-27T09:45:49.473651+00:00",
    "last_reported": "2025-10-29T09:52:09.392386+00:00",
    "last_updated": "2025-10-29T09:52:09.392386+00:00",
    "context": {
      "id": "01K8QP3JNGV6SF142NPB9552HJ",
      "parent_id": null,
      "user_id": null
    }
  }
    """


class DemoToolAgent(BaseToolAgent):
    def __init__(self):
        self.handler=PrivacyHandler()
    def get_tools(self) -> List[Callable]:
        tools=[get_info]
        return tools

    def call_tools(self, state: MessagesState):
        system_prompt="利用工具完成任务,部分数据可能已结经过隐私处理，被替换成@xx@格式。如果你需要使用该数据，请原样使用@xx@，后续我会进行解密"
        llm = PrivacyRunnableWrapper(get_llm())
        llm = llm.bind_tools(self.get_tools())
        system_message = {
            "role": "system",
            "content": system_prompt,
        }
        var=[system_message] + state["messages"]
        response = llm.invoke(var)

        return {"messages": [response]}


class PrivacyHandler:
    def __init__(self):
        # 预定义隐私类型（便于LLM识别，也可扩展）
        self.privacy_types = [
            "实体ID（entity_id）", "IP地址", "WiFi SSID（无线网络名称）",
            "时间戳（含时区的时间字符串）", "唯一标识符（id/context.id）",
            "设备状态值（如WiFi名称、IP等敏感状态）"
        ]
        self.not_privacy_types = [
            "friendly_name（设备名字）",
            "@xx@"
        ]
        self.encode_map=None
        self.decode_map =None

    def encode(self,content):
        if isinstance(content, str):
            self.get_encode_map(content)
            content=self.replace_text(content,self.encode_map)
        elif isinstance(content, list):
            var_str = ""
            for idx, message in enumerate(content):
                role = ""
                msg_content = ""
                # 处理LangChain消息对象（HumanMessage/AIMessage等）
                if isinstance(message, BaseMessage):
                    role = message.type  # 内置属性：user/assistant/system等
                    msg_content = message.content
                # 处理普通字典
                elif isinstance(message, dict):
                    role = message.get("role", "")  # 安全获取role，避免KeyError
                    msg_content = message.get("content", "")
                # 非预期类型：日志提示，跳过拼接
                else:
                    print(f"警告：索引{idx}的消息类型不支持content拼接，类型：{type(message)}")
                    continue

                # 拼接角色+内容（格式：角色: 内容\n，便于LLM识别上下文）
                if role and msg_content:
                    var_str += f"{role}: {msg_content}\n"
                elif msg_content:  # 无角色但有内容，仅拼接内容
                    var_str += f"{msg_content}\n"

            # 基于拼接的完整文本生成加密映射表
            if var_str.strip():  # 仅当有有效内容时生成映射表
                self.get_encode_map(var_str)
            for idx, message in enumerate(content):
                # 情况1：消息是LangChain的BaseMessage子类（HumanMessage/AIMessage等）
                if isinstance(message, BaseMessage):
                    message.content=self.replace_text(message.content,self.encode_map)
                # 情况2：消息是普通字典
                elif isinstance(message, dict) and "content" in message:
                    message["content"]=self.replace_text(message["content"],self.encode_map)
                # 情况3：非预期类型（日志提示+跳过）
                else:
                    print(f"警告：索引{idx}的消息类型不支持content替换，类型：{type(message)}")
        else:
            print(f"警告：不支持的类型")
        return content
    def decode(self,content):
        if isinstance(content, str):
            content=self.replace_text(content, self.decode_map)
        elif isinstance(content, list):
            for idx, message in enumerate(content):
                # 情况1：消息是LangChain的BaseMessage子类（HumanMessage/AIMessage等）
                if isinstance(message, BaseMessage):
                    message.content = self.replace_text(message.content, self.decode_map)
                # 情况2：消息是普通字典
                elif isinstance(message, dict) and "content" in message:
                    message["content"] = self.replace_text(message["content"], self.decode_map)
                # 情况3：非预期类型（日志提示+跳过）
                else:
                    print(f"警告：索引{idx}的消息类型不支持content替换，类型：{type(message)}")
        else:
            print(f"警告：不支持的类型")
        return content
    def get_encode_map(self, text: str) -> Dict[str, str]:
        """
        调用本地LLM识别文本中的隐私信息，并用语义变量替换，返回替换映射表
        :param text: 需要进行隐私处理的内容
        :return: encode_text - 原始隐私文本到语义变量的映射字典
        :raises ValueError: JSON解析失败或返回格式不符合要求时抛出
        """
        llm = get_llm()

        # 重构后的提示词（更清晰、指令更明确）
        system_prompt = f"""
        你是智能家居场景下的隐私信息处理助手，核心任务是精准识别文本中的隐私信息，并生成替换映射表。
        【核心规则】
        1. 隐私信息识别范参考（不局限于以下类型）：
           - {chr(10).join([f"- {t}" for t in self.privacy_types])}
        2. 非隐私信息识别范参考（不局限于以下类型）：
            -{chr(10).join([f"- {t}" for t in self.not_privacy_types])}
        3. 语义变量命名规范：
           - 优先使用语义化命名（如IP地址→ip_address、WiFi名称→wifi_ssid）；
           - 同类型重复项加序号（如多个ID→unique_id_01、unique_id_02，多个时间戳→timestamp_01）；
           - 变量名仅包含字母、数字、下划线，不使用特殊字符。
        4. 输出要求：
           - 仅返回JSON格式内容，无任何多余文本（如解释、说明、备注）；
           - JSON必须包含且仅包含"encoded_text"字段，值为键值对字典（key=原始隐私文本，value=语义变量）；
           - 确保JSON语法合法（无多余逗号、引号闭合），可直接被JSON解析器解析；
           - 非隐私信息（如"2.4G 无线"、"测试外网连通性"等普通文本）绝不替换。

        【正确示例】
        示例1（结构化JSON文本）：
        原始文本：
        {{
            "entity_id": "sensor.lumi_cn_551385025_mcn001_ip_address_p_2_2",
            "state": "192.168.43.141",
            "context": {{ "id": "01K96T2RKH7KPTX9RS21Z9973A" }}
        }}
        输出JSON：
        {{
            "encoded_text": {{
                "sensor.lumi_cn_551385025_mcn001_ip_address_p_2_2": "entity_id_01",
                "192.168.43.141": "ip_address",
                "01K96T2RKH7KPTX9RS21Z9973A": "unique_id_01"
            }}
        }}

        示例2（自然语言文本）：
        原始文本：
        当前网关IP：192.168.43.141，Wi-Fi SSID：shuashua，设备ID：01K96T2RKHMNWPKNM7WTG4RYQ9。
        输出JSON：
        {{
            "encoded_text": {{
                "192.168.43.141": "ip_address",
                "shuashua": "wifi_ssid",
                "01K96T2RKHMNWPKNM7WTG4RYQ9": "unique_id_01"
            }}
        }}
        """

        # 构造消息列表（符合LLM对话格式）
        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": f"请处理以下文本，严格按规则输出JSON格式的隐私替换映射表：\n{text}"}
        ]

        response = llm.invoke(messages).content
        # 提取纯JSON内容（处理LLM可能返回的多余文本）
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start == -1 or json_end == 0:
            raise ValueError(f"LLM返回内容无有效JSON：{response}")

        json_str = response[json_start:json_end]
        # 解析JSON
        result = json.loads(json_str)

        # 验证返回结构
        if "encoded_text" not in result or not isinstance(result["encoded_text"], dict):
            raise ValueError(f"返回JSON缺少'encoded_text'字段或类型错误：{result}")

        encode_text = result["encoded_text"]
        # 清理空值或无效映射（可选）
        encode_text = {k: v for k, v in encode_text.items() if k.strip() and v.strip()}
        encode_text = {k: f"@{v}@" for k, v in encode_text.items()}

        # 保存到实例变量
        self.encode_map = encode_text
        # 同时生成解密映射表
        self.get_decode_map()
        return encode_text

    def get_decode_map(self) -> Dict[str, str]:
        """
        将self.encode_map的键值对反转得到解密替换表（@语义变量@→原始值）
        注意：若加密表中存在多个原始值映射到同一个@语义变量@，后出现的会覆盖先出现的
        :return: decode_map - 解密映射表（@语义变量@→原始值）
        :raises ValueError: 未生成加密映射表时抛出
        """
        if self.encode_map is None:
            raise ValueError("加密映射表未生成，请先调用get_encode_map方法生成encode_map")

        # 反转键值对：原始逻辑（处理重复value时会覆盖）
        decode_map = {v: k for k, v in self.encode_map.items()}

        # 可选：检测重复的value并给出警告
        original_values = list(self.encode_map.values())
        duplicate_values = [v for v in original_values if original_values.count(v) > 1]
        if duplicate_values:
            print(f"警告：加密映射表中存在重复的语义变量 {set(duplicate_values)}，解密时会覆盖原始值")
        self.decode_map=decode_map
        return decode_map

    def replace_text(self, text: str, replace_map: Dict[str, str]) -> str:
        """
        基于映射表替换原文本中的信息（支持加密/解密双向替换）
        :param text: 原始文本
        :param replace_map: 替换映射表（加密：原始值→@语义变量@；解密：@语义变量@→原始值）
        :return: 替换后的文本
        """
        replaced_text = text
        # 按原始文本长度倒序替换（避免短文本匹配覆盖长文本）
        for original in sorted(replace_map.keys(), key=len, reverse=True):
            replaced_text = replaced_text.replace(original, replace_map[original])
        return replaced_text


if __name__ == "__main__":
    # DemoToolAgent().run_agent("光照强度？")
    text=None
    with open(r"F:\PyCharm\langchain_test\agent_project\temp_try\homeassitant_data\data\entities.json", 'r',
              encoding='utf-8') as f:
        text = json.dumps(json.load(f), ensure_ascii=False)
    print(text)
    print("========")
    print(PrivacyHandler().encode(text))
#     handler=PrivacyHandler()
#     test_text ="""当前光照强度如下：
#
# - 小米人体传感器2S（sensor.xiaomi_cn_blt_3_1ftnm7360c800_pir1_illumination_p_2_1005）：0.0 lx（最近上报时间 2025-11-04T07:54:10.536831+00:00）
# - 二楼卧室门窗传感器（sensor.isa_cn_blt_3_1md0u6qht0k00_dw2hl_illumination_p_2_1）：状态 “弱”"""
#     print("原始文本：", test_text)
#     # 1. 生成加密映射表
#     encode_map = handler.get_encode_map(test_text)
#     print("加密映射表：", encode_map)
#
#     # 2. 加密文本
#     encrypted_text = handler.replace_text(test_text, encode_map)
#     print("加密后文本：", encrypted_text)
#
#     # 3. 生成解密映射表
#     decode_map = handler.get_decode_map()
#     print("解密映射表：", decode_map)
#
#     # 4. 解密文本
#     decrypted_text = handler.replace_text(encrypted_text, decode_map)
#     print("解密后文本：", decrypted_text)