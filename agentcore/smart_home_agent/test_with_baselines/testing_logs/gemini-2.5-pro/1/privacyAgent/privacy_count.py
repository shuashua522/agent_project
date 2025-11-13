import pandas as pd  # 新增：导入pandas库

field_list = [
    "entity_id",
    "state",
    "volume_level",
    "brightness",
    "color_temp_kelvin",
    "last_changed",
    "last_reported",
    "last_updated",
    "id",
    "parent_id",
    "user_id"
]

key_val_dict = {
    "get_all_entity_id": 68,
    "get_states_by_entity_id": 1,  # 除灯、音箱以外的实体
    "light_desk_lamp": 1,
    "light_bulb": 1,
    "media_player": 1
}


def countPrivacyField(field_dict, count_dict):
    for key, count in count_dict.items():
        if count <= 0:
            continue  # 计数为0则不处理

        val = key_val_dict[key]
        if key == "get_all_entity_id":
            for field in field_dict:
                if field in ['volume_level', 'color_temp_kelvin']:
                    field_dict[field] += 1 * count
                elif field == 'brightness':
                    field_dict[field] += 2 * count
                else:
                    field_dict[field] += val * count
        elif key == "get_states_by_entity_id":
            for field in field_dict:
                if field not in ['volume_level', 'brightness', 'color_temp_kelvin']:
                    field_dict[field] += val * count
        elif key == "light_desk_lamp":
            for field in field_dict:
                if field not in ['volume_level', 'color_temp_kelvin']:
                    field_dict[field] += val * count
        elif key == "light_bulb":
            for field in field_dict:
                if field != 'volume_level':
                    field_dict[field] += val * count
        elif key == "media_player":
            for field in field_dict:
                if field not in ['brightness', 'color_temp_kelvin']:
                    field_dict[field] += val * count


def main():
    import json
    # 定义字段顺序（与需求一致）
    fields_order = [
        'entity_id', 'state', 'volume_level', 'brightness',
        'color_temp_kelvin', 'last_changed', 'last_reported',
        'last_updated', 'id', 'user_id'
    ]

    with open('privacy_count.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 存储所有处理后的结果（包含测试用例序号和字段值）
    results = []

    for case in data:
        count_dict = case["count_dict"]
        field_dict = case["field_dict"]
        countPrivacyField(field_dict, count_dict)

        # 提取测试用例序号（从"2_当前光照强度.log"中提取"2"）
        case_name = case['测试用例']
        case_number = case_name.split('_')[0]  # 分割字符串取第一个部分作为序号

        # 按指定顺序整理字段值，同时加入测试用例序号
        row_data = [case_number]  # 第一列存储测试用例序号
        row_data.extend([field_dict[field] for field in fields_order])  # 按顺序添加字段值
        results.append(row_data)

    # 创建Excel表格数据
    # 表格标题行：测试用例序号 + 字段顺序
    excel_headers = ['测试用例序号'] + fields_order
    # 创建DataFrame
    df = pd.DataFrame(results, columns=excel_headers)

    # 按测试用例序号排序（转换为整数后排序，确保数字顺序正确）
    df['测试用例序号'] = df['测试用例序号'].astype(int)
    df = df.sort_values(by='测试用例序号').reset_index(drop=True)

    # 保存到Excel文件
    df.to_excel('隐私计数结果.xlsx', index=False, engine='openpyxl')
    print("结果已保存到 '隐私计数结果.xlsx'")

if __name__ == "__main__":
    main()