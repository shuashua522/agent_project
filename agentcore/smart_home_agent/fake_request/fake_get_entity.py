import json
import os

# 获取当前 Python 文件所在目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 拼接 entities.json 和 services.json 的绝对路径
entities_path = os.path.join(current_dir, "entities.json")
services_path = os.path.join(current_dir, "services.json")

# 读取 JSON 文件
entities = json.load(open(entities_path, "r", encoding="utf-8"))
services = json.load(open(services_path, "r", encoding="utf-8"))


def fake_get_services_by_domain(domain:str):
    for service in services:
        if domain == service["domain"]:
            return service
    return None
def fake_get_all_entities():
    return entities

def fake_get_states_by_entity_id(entity_id):
    for entity in entities:
        if entity.get("entity_id") == entity_id:  # 使用get避免KeyError
            return entity
    # todo 是这样吗？还是会报错
    # 若未找到匹配项，返回None
    return None

def test_():
    entity = fake_get_states_by_entity_id("switch.cuco_cn_269067598_cp1_on_p_2_1")
    entity['state'] = "on"
if __name__ == "__main__":
    print(fake_get_all_entities())
    print(fake_get_states_by_entity_id("switch.cuco_cn_269067598_cp1_on_p_2_1"))
    print(fake_get_services_by_domain("light"))