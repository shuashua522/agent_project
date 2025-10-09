# 模拟数据的文件所在目录
from bin.config import set_environment_variables
import json
import os
from collections import OrderedDict

import requests

mock_data_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),  # 当前文件所在目录
    'test_mock_data'  # 子目录（无开头斜杠）
)
token=os.getenv("HOMEASSITANT_AUTHORIZATION_TOKEN")
server=os.getenv("HOMEASSITANT_SERVER")
active_project_env=os.getenv("ACTIVE_PROJECT_ENV")

class Device_info_doc:
    def __init__(self):
        """初始化类，加载所有需要的JSON数据"""
        self.mock_data_dir = mock_data_dir

        # TODO 逻辑待修改
        self.device_registry = self._load_json('device_registry.json')
        self.entity_registry = self._load_json('entity_registry.json')

        self.selected_entities = self._load_selected_entities() # ok

        # 初始化各类映射结果
        self.entity_ids = self.get_all_entity_ids()  # ok
        self.entity_info_strings=self.get_entity_info_strings() #ok
        self.entity_capabilities_strings=self.get_entity_capabilities_strings() #ok

        self.device_id2name = self.extract_device_info()

        self.device_entity_map = self.get_device_entities()
        self.device_capability_map = self.get_device_capabilities()

        self.all_capabilities_str=self.get_all_capabilities_str()
        self.device_info_strings=self.get_device_info_strings()
    # TODO
    def _load_device_registry(self):
        pass
    def _load_entity_registry(self):
        pass
    def _load_selected_entities(self):
        if active_project_env == "dev":
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            url = f"http://{server}/api/states"

            # 发送GET请求
            response = requests.get(url, headers=headers)
            # 检查请求是否成功
            response.raise_for_status()
            # 返回JSON响应内容
            return response.json()
        elif active_project_env == "test":
            self._load_json('selected_entities.json')
    def get_entity_info_strings(self):
        """
        生成格式为 "{entity_id} ({friendly_name}): {capability}" 的字符串，
        各实体信息以换行符分隔，capability 为 entity_id 中 '.' 前面的部分
        """
        formatted_entities = []
        for entity in self.selected_entities:
            # 提取entity_id
            entity_id = entity.get("entity_id", "")

            # 提取friendly_name（默认值为"Unknown"以防缺失）
            friendly_name = entity.get("attributes", {}).get("friendly_name", "Unknown")

            # 提取capability（取entity_id中'.'前面的部分）
            if "." in entity_id:
                capability = entity_id.split(".")[0]
            else:
                # 处理没有'.'的异常情况，直接使用完整entity_id
                capability = entity_id

            # 按照指定格式生成字符串并添加到列表
            formatted_str = f"{entity_id} ({friendly_name}): {capability}"
            formatted_entities.append(formatted_str)

        # 将列表转换为以换行符分隔的字符串
        return '\n'.join(formatted_entities)

    def get_entity_capabilities_strings(self):
        """
        提取self.selected_entities中所有实体的capability（entity_id中'.'前面的部分），
        去重后转换为以换行符分隔的字符串
        """
        # 使用set存储capability以实现自动去重
        capabilities = set()

        for entity in self.selected_entities:
            entity_id = entity.get("entity_id", "")
            # 提取capability（取entity_id中'.'前面的部分）
            if "." in entity_id:
                capability = entity_id.split(".")[0]
            else:
                # 处理没有'.'的异常情况，直接使用完整entity_id
                capability = entity_id

            # 仅添加非空值
            if capability:
                capabilities.add(capability)

        # 将set转换为以换行符分隔的字符串
        return '\n'.join(capabilities)
    def get_all_capabilities_str(self):
        """
        从device_capability_map中提取所有能力，去重后用\n分隔为字符串

        返回:
            str: 所有去重后的能力，用换行符分隔；若没有能力则返回空字符串
        """
        # 用字典键存储所有能力（自动去重且保持首次出现顺序，Python 3.7+）
        all_capabilities = {}

        # 遍历所有设备的能力列表
        for capabilities in self.device_capability_map.values():
            for cap in capabilities:
                all_capabilities[cap] = None  # 仅用键存储能力

        # 将能力列表转为用\n分隔的字符串
        return '\n'.join(all_capabilities.keys())
    def _load_json(self, filename):
        """内部辅助方法，加载JSON文件"""
        file_path = os.path.join(self.mock_data_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误：未找到文件 {file_path}")
            return None
        except json.JSONDecodeError:
            print(f"错误：{file_path} 不是有效的JSON文件")
            return None

    def extract_device_info(self):
        """从device_registry中提取设备ID和名称，返回有序字典"""
        device_dict = OrderedDict()
        if not self.device_registry:
            return device_dict

        # 遍历设备列表，提取id和name
        for device in self.device_registry.get('data', {}).get('devices', []):
            device_id = device.get('id')
            device_name = device.get('name')
            if device_id and device_name:  # 确保id和name都存在
                device_dict[device_id] = device_name

        return device_dict

    def get_all_entity_ids(self):
        """从selected_entities中提取所有entity_id，返回有序列表"""
        if not self.selected_entities:
            return []
        return [item['entity_id'] for item in self.selected_entities if 'entity_id' in item]

    def get_device_entities(self):
        """构建device_id到entity_id列表的映射"""
        device_entity_map = {}
        if not self.entity_registry or not self.entity_ids:
            return device_entity_map

        # 遍历所有实体
        for entity in self.entity_registry.get('data', {}).get('entities', []):
            entity_id = entity.get('entity_id')
            device_id = entity.get('device_id')

            # 只处理在指定entity_ids列表中的实体
            if entity_id in self.entity_ids:
                if device_id not in device_entity_map:
                    device_entity_map[device_id] = []
                device_entity_map[device_id].append(entity_id)

        return device_entity_map

    def get_device_capabilities(self):
        """提取设备能力映射（entity_id前缀）"""
        device_capability_map = {}
        if not self.device_entity_map:
            return device_capability_map

        for device_id, entity_ids in self.device_entity_map.items():
            # 使用字典保持插入顺序并去重（Python 3.7+）
            capability_dict = {}
            for entity_id in entity_ids:
                capability = entity_id.split('.')[0]
                capability_dict[capability] = None  # 仅用键存储能力
            device_capability_map[device_id] = list(capability_dict.keys())

        return device_capability_map

    def get_device_info_strings(self):
        """
        生成包含设备ID、名称和能力的字符串列表，并用\n分隔返回

        返回:
            str: 所有设备信息字符串，每条信息占一行；若没有设备则返回空字符串
        """
        device_strings = []

        # 遍历设备能力映射，组合设备信息
        for device_id, capabilities in self.device_capability_map.items():
            # 获取设备名称，若不存在则使用"未知设备"作为默认值
            device_name = self.device_id2name.get(device_id, "未知设备")

            # 按照指定格式组合字符串
            device_str = f"{device_id} ({device_name}): {','.join(capabilities)}"
            device_strings.append(device_str)

        # 将所有设备字符串用换行符连接
        return '\n'.join(device_strings)

DEVICE_INFO_DOC=Device_info_doc()
# print(DEVICE_INFO_DOC.entity_info_strings)
# print(DEVICE_INFO_DOC.entity_capabilities_strings)
# print(DEVICE_INFO_DOC.all_capabilities_str)
# print(DEVICE_INFO_DOC.device_info_strings)

