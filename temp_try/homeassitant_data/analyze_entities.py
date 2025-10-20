import json

from agent_project.agentcore.smart_home_agent.privacy_handler import PrivacyHandler


def write_list_to_json(lst: list, file_path: str):
    """
    将列表写入JSON文件

    参数:
        lst: 要写入的列表
        file_path: 目标JSON文件的路径（如"output.json"）
    """
    # 使用with语句打开文件，自动处理文件关闭
    with open(file_path, 'w', encoding='utf-8') as f:
        # 调用json.dump()将列表写入文件
        # indent=4 用于格式化输出（可选，让JSON更易读）
        json.dump(lst, f, ensure_ascii=False, indent=4)

# JSON文件路径（相对路径或绝对路径）
file_path = "data/entities.json"

# 打开文件并读取（指定encoding='utf-8'避免中文乱码）
with open(file_path, "r", encoding="utf-8") as f:
    # 解析JSON内容为Python对象（此处是字典）
    data = json.load(f)

# 打印解析后的数据
print("读取到的JSON数据：")
print(data)

key_set=set()
privacyHandler=PrivacyHandler()
for entity in data:
    # print(type(entity["context"]))
    key_set.update(entity)

    # print(privacyHandler.encodeEntity(entity))
    # print(privacyHandler.generate_state_brief_description(entity))

encode_entities=privacyHandler.encodeEntities(data)
print(encode_entities)
write_list_to_json(encode_entities,"data/encode_entities")

decode_entities=privacyHandler.decodeEntities(encode_entities)
print(decode_entities)
write_list_to_json(decode_entities,"data/decode_entities")
print(key_set)
