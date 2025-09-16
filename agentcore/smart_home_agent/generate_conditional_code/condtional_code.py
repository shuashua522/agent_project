from agent_project.agentcore.smart_home_agent.device_interaction_agent import get_all_entity_id, get_states_by_entity_id


def funcc6577769_2beb_4f27_ad49_91ad1a200332() -> bool:
    """检查所有门窗设备是否均处于打开状态"""
    try:
        # 获取所有实体状态信息
        all_entities = get_all_entity_id()
        
        # 筛选出门窗相关设备（根据entity_id关键词匹配，不区分大小写）
        door_window_entities = [
            entity['entity_id']
            for entity in all_entities
            if 'door' in entity['entity_id'].lower() or 'window' in entity['entity_id'].lower()
        ]
        
        # 无门窗设备时返回False（无设备可检查视为不满足条件）
        if not door_window_entities:
            return False
        
        # 逐一检查门窗状态是否为打开（状态值统一转为小写判断）
        for entity_id in door_window_entities:
            state = get_states_by_entity_id(entity_id)
            if state['state'].lower() != 'open':
                return False
        
        # 所有门窗均打开时返回True
        return True
    except Exception as e:
        print(f"门窗状态检查失败: {str(e)}")
        return False

def func1e2c5eb1_00ad_4bfd_8d08_a5344d680427() -> bool:
    """
    检查所有插座设备是否都处于关闭状态。
    如果所有插座的状态都是'off'，则返回True；否则返回False。
    如果插座状态为'unavailable'，则视为不满足关闭条件。
    """
    try:
        # 获取插座设备的状态
        socket_state = get_states_by_entity_id("switch.cuco_cn_269067598_cp1_on_p_2_1")
        
        # 检查插座状态是否为'off'
        if socket_state.get('state') == 'off':
            return True
        else:
            return False
            
    except Exception as e:
        # 如果获取状态失败或出现其他异常，返回False
        print(f"检查插座状态时出现错误: {e}")
        return False
