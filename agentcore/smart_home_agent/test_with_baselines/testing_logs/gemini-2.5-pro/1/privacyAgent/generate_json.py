import json
import os
import re

# 定义基础字典结构
count_dict = {
    "get_all_entity_id": 0,
    "get_states_by_entity_id": 0,
    "light_desk_lamp": 0,
    "light_bulb": 0,
    "media_player": 0
}

field_dict = {
    'entity_id': 0,
    'state': 0,
    'volume_level': 0,
    'brightness': 0,
    'color_temp_kelvin': 0,
    'last_changed': 0,
    'last_reported': 0,
    'last_updated': 0,
    'id': 0,
    'user_id': 0
}

# 匹配文件名格式：数字_任意字符.log
pattern = re.compile(r'^(\d+)_.+\.log$')

# 获取当前目录下符合条件的文件并提取序号
matched_files = []
for filename in os.listdir('.'):
    if os.path.isfile(filename) and pattern.match(filename):
        # 提取文件名中的数字序号用于排序
        number = int(pattern.match(filename).group(1))
        matched_files.append((number, filename))

# 按序号排序（确保按数字顺序排列）
matched_files.sort(key=lambda x: x[0])

# 生成数据（最多50条）
data = []
for num, filename in matched_files[:50]:
    data.append({
        "测试用例": filename,  # 直接使用文件名作为值
        "count_dict": count_dict.copy(),
        "field_dict": field_dict.copy()
    })

# 写入JSON文件
with open('privacy_count.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"已生成JSON文件：test_cases.json（包含 {len(data)} 个测试用例）")