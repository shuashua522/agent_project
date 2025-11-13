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
field_dict = {'entity_id': 0, 'state': 0, 'volume_level': 0, 'brightness': 0, 'color_temp_kelvin': 0, 'last_changed': 0,
              'last_reported': 0, 'last_updated': 0, 'id': 0, 'user_id': 0}

key_val_dict = {
    "get_all_entity_id": 68,
    "get_states_by_entity_id": 1, # 除灯、音箱以外的实体
    "light_desk_lamp": 1,
    "light_bulb": 1,
    "media_player": 1
}
count_dict = {
    "get_all_entity_id": 0,
    "get_states_by_entity_id": 0,
    "light_desk_lamp": 0,
    "light_bulb": 0,
    "media_player": 0
}

# 根据count_dict和key_val_dict为field_dict补充计数
for key, count in count_dict.items():
    if count <= 0:
        continue  # 计数为0则不处理

    val = key_val_dict[key]
    if key == "get_all_entity_id":
        # 除'volume_level', 'brightness', 'color_temp_kelvin'外，所有值加68
        # 'volume_level'和'color_temp_kelvin'加1，'brightness'加2
        for field in field_dict:
            if field in ['volume_level', 'color_temp_kelvin']:
                field_dict[field] += 1 * count
            elif field == 'brightness':
                field_dict[field] += 2 * count
            else:
                field_dict[field] += val * count
    elif key == "get_states_by_entity_id":
        # 除'volume_level', 'brightness', 'color_temp_kelvin'外，所有值加1
        for field in field_dict:
            if field not in ['volume_level', 'brightness', 'color_temp_kelvin']:
                field_dict[field] += val * count
    elif key == "light_desk_lamp":
        # 除'volume_level', 'color_temp_kelvin'外加1
        for field in field_dict:
            if field not in ['volume_level', 'color_temp_kelvin']:
                field_dict[field] += val * count
    elif key == "light_bulb":
        # 除'volume_level'外所有值加1
        for field in field_dict:
            if field != 'volume_level':
                field_dict[field] += val * count
    elif key == "media_player":
        # 除 'brightness', 'color_temp_kelvin'外，所有值加1
        for field in field_dict:
            if field not in ['brightness', 'color_temp_kelvin']:
                field_dict[field] += val * count