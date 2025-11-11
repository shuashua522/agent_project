from agent_project.agentcore.smart_home_agent.test_with_baselines.devices_init import case_01_env, case_02_env, \
    case_03_env, send_speaker_command, turn_on_bulb, turn_off_bulb, turn_off_desk_lamp, turn_on_desk_lamp, turn_on_plug, \
    turn_off_plug, enable_test_memory, disable_test_memory


def init_devices(*pre_functions):
    """装饰器工厂：在目标函数执行前调用前置函数，并将被装饰函数注册到列表中"""
    # 初始化一个列表，用于存储所有被装饰的函数（按出现顺序）
    if not hasattr(init_devices, "registered_functions"):
        init_devices.registered_functions = []

    def decorator(func):
        def wrapper(*args, **kwargs):
            # 先执行所有前置函数
            for pre_func in pre_functions:
                pre_func()
            # 再执行目标函数
            return func(*args, **kwargs)

        # 将被装饰后的函数（wrapper）加入注册列表（保持定义顺序）
        init_devices.registered_functions.append(wrapper)
        return wrapper

    return decorator

# 修改代码（将原代码中的return注释掉，重写return，return的内容为原return的英文。其余代码不做改动），返回Python代码格式：
# ------------------------------
# 状态查询
# ------------------------------
# 1. 网络状况
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def check_network():
    # return "网络状况"
    return "Network status"

# 2. 当前光照强度
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def check_light_intensity():
    # return "当前光照强度"
    return "Current light intensity"

# 3. 人体传感器需要换电池了吗？
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def check_human_sensor_battery():
    # return "人体传感器需要换电池了吗？"
    return "Does the human body sensor need a battery replacement?"

# 4. 窗户开着吗？
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def check_window_status():
    # return "窗户开着吗？"
    return "Is the window open?"

# 5. 所有的灯都亮了吗？
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def check_all_lights():
    # return "所有的灯都亮了吗？"
    return "Are all the lights on?"

# 6. 台灯处于什么情况
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def check_desk_lamp():
    # return "台灯处于什么情况"
    return "What is the status of the desk lamp"

# ------------------------------
# 简单设备控制
# ------------------------------

# 1. 函数：返回“打开台灯和智能插座”
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def open_desk_lamp_socket():
    # return "打开台灯和智能插座。"
    return "Turn on the desk lamp and smart socket."

# 2. 函数：返回“关闭所有灯光”
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def close_all_lights():
    # return "关闭所有灯光。"
    return "Turn off all lights."

# 3. 函数：返回“关掉音乐”
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def turn_off_music():
    # return "关掉音乐。"
    return "Turn off the music."

# ------------------------------
# 复杂设备控制 - 调节
# ------------------------------

# 1. 将整个房子变暗
@init_devices(lambda:disable_test_memory(),lambda:case_02_env())
def dim_entire_house():
    # return "将整个房子变暗"
    return "Dim the entire house"

# 2. 台灯太亮了，调暗到当前值的1/3
@init_devices(lambda:disable_test_memory(),lambda:case_02_env())
def dim_desk_lamp_to_third():
    # return "台灯太亮了，调暗到当前值的1/3"
    return "The desk lamp is too bright, dim it to 1/3 of the current value"

# 3. 把客厅灯亮度调到50%
@init_devices(lambda:disable_test_memory(),lambda:case_02_env())
def set_living_room_light_to_50():
    # return "把客厅灯亮度调到50%"
    return "Set the brightness of the living room light to 50%"

# 4. 调高音箱音量，并把灯泡调暗。
@init_devices(lambda:disable_test_memory(),lambda:case_02_env())
def increase_speaker_volume_and_dim_bulb():
    # return "调高音箱音量，并把灯泡调暗。"
    return "Increase the speaker volume and dim the bulb."

# 5. 把客厅灯调暖一点
@init_devices(lambda:disable_test_memory(),lambda:case_02_env())
def warm_living_room_light():
    # return "把客厅灯调暖一点"
    return "Make the living room light a bit warmer"

# 6. 播放晴天，关闭台灯。
@init_devices(lambda:disable_test_memory(),lambda:case_02_env())
def play_sunny_and_close_desk_lamp():
    # return "播放晴天，关闭台灯。"
    return "Play \"Sunny\" and turn off the desk lamp."

# 7. 打开台灯，但保持网关灯亮着。
@init_devices(lambda:disable_test_memory(),lambda:case_02_env())
def turn_on_desk_lamp_keep_gateway_on():
    # return "打开台灯，但保持网关灯亮着。"
    return "Turn on the desk lamp, but keep the gateway light on."

# 8. 把卧室灯关掉，打开客厅灯
@init_devices(lambda:disable_test_memory(),lambda:case_02_env())
def turn_off_bedroom_light_turn_on_living_room():
    # return "把卧室灯关掉，打开客厅灯"
    return "Turn off the bedroom light and turn on the living room light"

# ------------------------------
# 音乐与音频控制
# ------------------------------
# 1. 切换下一首歌
@init_devices(lambda:disable_test_memory(),lambda:case_03_env())
def switch_to_next_song():
    # return "切换下一首歌"
    return "Switch to the next song"

# 2. 音量下调2%
@init_devices(lambda:disable_test_memory(),lambda:case_03_env())
def lower_volume_by_2percent():
    # return "音量下调2%"
    return "Lower the volume by 2%"

# 3. 打开电台
@init_devices(lambda:disable_test_memory(),lambda:case_03_env())
def turn_on_radio():
    # return "打开电台"
    return "Turn on the radio"

# 4. 暂停播放
@init_devices(lambda:disable_test_memory(),lambda:case_03_env())
def pause_playback():
    # return "暂停播放"
    return "Pause playback"

# 5. 刚刚那首歌听着不错，我想再听一遍
@init_devices(lambda:disable_test_memory(),lambda:case_03_env())
def replay_previous_song():
    # return "刚刚那首歌听着不错，我想再听一遍"
    return "That song was good, I want to listen to it again"

# 6. 放一首英文歌
@init_devices(lambda:disable_test_memory(),lambda:case_03_env())
def play_english_song():
    # return "放一首英文歌"
    return "Play an English song"


# ------------------------------
# 自动化 - 触发器
# ------------------------------
# 1. 当有人经过时，把灯打开
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def turn_on_light_when_person_passes():
    # return "当有人经过时，把灯打开"
    return "When someone passes by, turn on the light"

# 2. 当音箱关闭时，打开台灯
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def turn_on_desk_lamp_when_speaker_off():
    # return "当音箱关闭时，打开台灯"
    return "When the speaker is off, turn on the desk lamp"

# 3. 天黑时，如果窗户没关，告诉我。
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def notify_if_window_open_at_night():
    # return "天黑时，如果窗户没关，告诉我。"
    return "When it's dark, if the window is not closed, tell me."

# 4. 当台灯打开时，打开插座
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def turn_on_socket_when_desk_lamp_on():
    # return "当台灯打开时，打开插座"
    return "When the desk lamp is on, turn on the socket"

# 5. 如果5分钟没有检测到人，就关闭所有灯。
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def turn_off_all_lights_if_no_person_for_5min():
    # return "如果5分钟没有检测到人，就关闭所有灯。"
    return "If no one is detected for 5 minutes, turn off all the lights."

# 6. 当客厅窗户关闭时，关闭智能插座。
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def turn_off_smart_socket_when_living_window_closed():
    # return "当客厅窗户关闭时，关闭智能插座。"
    return "When the living room window is closed, turn off the smart socket."

# 7. 如果门窗传感器打开，在音箱上提醒我。
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def remind_on_speaker_if_door_window_sensor_open():
    # return "如果门窗传感器打开，在音箱上提醒我。"
    return "If the door and window sensor is open, remind me on the speaker."

# 8. 如果客厅窗户打开超过 30 分钟，通知我。
@init_devices(lambda:disable_test_memory(),lambda:case_01_env())
def notify_if_living_window_open_over_30min():
    # return "如果客厅窗户打开超过 30 分钟，通知我。"
    return "If the living room window is open for more than 30 minutes, notify me."

# ------------------------------
# 个性化与偏好
# ------------------------------
# 1. 太安静了，放点音乐
@init_devices(lambda:enable_test_memory(),lambda:send_speaker_command("关闭音箱"))
def play_music_when_quiet():
    # return "太安静了，放点音乐"
    return "It's too quiet, play some music"

# 2. 打开床边灯
@init_devices(lambda:enable_test_memory(),lambda:turn_off_bulb(),lambda:turn_off_desk_lamp())
def turn_on_bedside_light():
    # return "打开床边灯"
    return "Turn on the bedside light"

# 3. 我要睡觉了
@init_devices(lambda:enable_test_memory(),lambda:turn_on_bulb(40,4000),lambda:turn_on_desk_lamp(40))
def going_to_sleep():
    # return "我要睡觉了"
    return "I'm going to sleep"

# 4. 我正在接电话，调一下音箱的音量
@init_devices(lambda:enable_test_memory(),lambda:send_speaker_command("播放晴天"))
def adjust_speaker_volume_while_on_call():
    # return "我正在接电话，调一下音箱的音量"
    return "I'm on a call, adjust the speaker volume"

# 5. 我要起夜，灯开一下
@init_devices(lambda:enable_test_memory(),lambda:turn_off_bulb(),lambda:turn_off_desk_lamp())
def turn_on_light_for_nighttime_visit():
    # return "我要起夜，灯开一下"
    return "I need to get up at night, turn on the light"

# 6. 准备出门。关闭所有非必要的设备。
@init_devices(lambda:enable_test_memory(),lambda:send_speaker_command("播放晴天"),lambda:turn_on_bulb(40,4000),
              lambda:turn_on_desk_lamp(40),lambda:turn_on_plug())
def turn_off_unnecessary_devices_before_leaving():
    # return "准备出门。关闭所有非必要的设备。"
    return "Getting ready to go out. Turn off all non-essential devices."

# 7. 我要开始看书了，把灯调到合适模式
@init_devices(lambda:enable_test_memory(),lambda:turn_off_bulb(),lambda:turn_off_desk_lamp())
def set_light_to_reading_mode():
    # return "我要开始看书了，把灯调到合适模式"
    return "I'm going to start reading, set the light to the appropriate mode"

# 8. 将客厅灯调至我最喜欢的色温。
@init_devices(lambda:enable_test_memory(),lambda:turn_off_bulb(),lambda:turn_off_desk_lamp())
def set_living_room_light_to_favorite_color_temp():
    # return "将客厅灯调至我最喜欢的色温。"
    return "Set the living room light to my favorite color temperature."

# 9. 我回家了
@init_devices(lambda:enable_test_memory(),lambda:turn_off_bulb(),lambda:turn_off_desk_lamp(),lambda:send_speaker_command("关闭音箱"))
def i_am_home():
    # return "我回家了"
    return "I'm home"

# 10. 我想听个故事
@init_devices(lambda:enable_test_memory(),lambda:send_speaker_command("关闭音箱"))
def want_to_hear_a_story():
    # return "我想听个故事"
    return "I want to hear a story"

# 11. 网关如果连的不是我的网络，把所有灯关掉，然后再打开，吓吓他
@init_devices(lambda:enable_test_memory(),lambda:turn_on_bulb(40,4000),
              lambda:turn_on_desk_lamp(40),)
def scare_intruder_with_lights_if_wrong_network():
    # return "网关如果连的不是我的网络，把所有灯关掉，然后再打开，吓吓他"
    return "If the gateway is not connected to my network, turn off all lights and then turn them on again to scare him"

# 12. 为家里营造万圣节气氛。
@init_devices(lambda:enable_test_memory(),lambda:turn_off_bulb(),lambda:turn_off_desk_lamp())
def create_halloween_atmosphere():
    # return "为家里营造万圣节气氛。"
    return "Create a Halloween atmosphere at home."

# 13. 关闭氛围组设备
@init_devices(lambda:enable_test_memory(),lambda:turn_on_bulb(40,4000),lambda:send_speaker_command("打开音箱"))
def turn_off_atmosphere_devices():
    # return "关闭氛围组设备"
    return "Turn off the atmosphere group devices"

# 14. 我的服务器居然没响应了，你有什么头绪吗？（测试前需关闭插座）
@init_devices(lambda:enable_test_memory(),lambda:turn_off_plug())
def check_server_issue_with_socket_off():
    # return "我的服务器居然没响应了，你有什么头绪吗？"
    return "My server is actually unresponsive, do you have any ideas?"

# 15. 准备睡觉
@init_devices(lambda:enable_test_memory(),lambda:turn_off_bulb(),lambda:turn_on_desk_lamp(40))
def prepare_to_sleep():
    # return "准备睡觉"
    return "Prepare to sleep"

# 16. 现在是周六晚上了，明天记得叫我起床。
@init_devices(lambda:enable_test_memory())
def remind_to_wake_up_sunday():
    # return "现在是周六晚上了，明天记得叫我起床。"
    return "It's Saturday night now, remember to wake me up tomorrow."

# 17. 又到暑假了，现在我准备睡觉了。我有错过什么吗？（门窗传感器关闭）
@init_devices(lambda:enable_test_memory())
def check_missed_events_before_sleep_in_summer_vacation():
    # return "又到暑假了，现在我准备睡觉了。我有错过什么吗？"
    return "It's summer vacation again, now I'm ready to sleep. Did I miss anything?"

# 18. 帮我配置下网关的勿扰模式
@init_devices(lambda:enable_test_memory())
def configure_gateway_do_not_disturb_mode():
    # return "帮我配置下网关的勿扰模式"
    return "Help me configure the gateway's Do Not Disturb mode"

# 19. 哦，今天天气真好
@init_devices(lambda:enable_test_memory())
def comment_on_nice_weather():
    # return "哦，今天天气真好"
    return "Oh, the weather is really nice today"


###################################################################
"""demo
# 定义前置操作函数
def open_door():
    print("执行：开门")


def down_light(name):
    print(f"执行：关闭{name}")


def start_machine():
    print("执行：启动机器")


# 被@init_devices装饰的函数（按出现顺序注册）
@init_devices(lambda: open_door())  # 前置操作：开门
def func_a():
   return "执行函数A"


@init_devices(lambda: down_light("客厅灯"), lambda: start_machine())  # 前置操作：关客厅灯 → 启动机器
def func_b():
    return "执行函数B"


@init_devices()  # 无前置操作
def func_c():
    return "执行函数C"

"""
# 按注册顺序（即函数出现顺序）调用所有被装饰的函数
if __name__ == "__main__":
    print("===== 开始按顺序执行所有被装饰的函数 =====")
    for func in init_devices.registered_functions:
        # s=func()
        print(func())
        print("----- 分隔线 -----")