import os
import re
import traceback

import requests

from agent_project.agentcore.commons.utils import get_context_logger
from agent_project.agentcore.smart_home_agent.smart_home_agent_entry import SmartHomeAgent
from agent_project.agentcore.smart_home_agent.test_with_baselines.baselines_homeassitant.sashaAgent import \
    run_sashaAgent
from agent_project.agentcore.smart_home_agent.test_with_baselines.baselines_homeassitant.singleAgent import SingleAgent
from agent_project.agentcore.config.global_config import HOMEASSITANT_AUTHORIZATION_TOKEN, HOMEASSITANT_SERVER, \
    ACTIVE_PROJECT_ENV
import agent_project.agentcore.config.global_config as global_config

token=HOMEASSITANT_AUTHORIZATION_TOKEN
server=HOMEASSITANT_SERVER
active_project_env=ACTIVE_PROJECT_ENV
def execute_domain_service_by_entity_id(domain,service,body,
    ) :
    """
    Calls a service within a specific domain. Will return when the service has been executed.

    Returns a list of states that have changed while the service was being executed, and optionally response data, if supported by the service.
    """
    if active_project_env == "dev":
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"http://{server}/api/services/{domain}/{service}"
        # 设置请求体数据
        # payload = {
        #     "entity_id": entity_id
        # }
        payload = body

        # 发送POST请求
        response = requests.post(
            url=url,
            json=payload,  # 自动将字典转换为JSON并设置正确的Content-Type
            headers=headers
        )
        # 检查请求是否成功
        response.raise_for_status()
        # 返回JSON响应
        return response.json()
# 获取当前文件的绝对路径
current_file_path = os.path.abspath(__file__)
# 定位到所在目录
current_dir = os.path.dirname(current_file_path)
testing_logs_dir = os.path.join(current_dir, "testing_logs")

entitys_map={
    "灯泡":"light.yeelink_cn_1162511951_mbulb3_s_2",
}
testcases=["将整个房子变暗","网络状况","台灯太亮了，调一下亮度","所有的灯都亮了吗？",
           "打开插座","当前光照强度","我要睡觉了","准备出门。关闭所有非必要的设备。",
           "我要起夜，台灯开一下","10分钟后关闭台灯","我要开始学习了，每40分钟提醒我休息"]

def init_test_config():
    """测试前都要初始化测试环境"""
    # TODO
    pass

def init_devices_states():
    """每次测试前都要初始化设备状态
    台灯三个mode：
    mode 0： 似乎无效？保持上一个状态？
    mode 1： 起夜
    mode 2： 休闲
    """
    # 插座初始化
    body = {
        "entity_id": "switch.cuco_cn_269067598_cp1_on_p_2_1"
    }
    execute_domain_service_by_entity_id("switch", "turn_on", body)
    # 灯泡初始化
    body={
        "entity_id": "light.yeelink_cn_1162511951_mbulb3_s_2",
        "color_temp_kelvin": 4000,
        "brightness_pct": 30
    }
    execute_domain_service_by_entity_id("light","turn_on",body)
    # 台灯初始化
    body={
        "entity_id": "light.philips_cn_1061200910_lite_s_2",
        # "brightness_pct": 70,
        "effect": "mode 2"
    }
    execute_domain_service_by_entity_id("light","turn_on",body)

def process_testcases(agent_name,dir_path=testing_logs_dir,):
    """
    遍历测试用例
    agent_name取值：[singleAgent,sashaAgent,ourAgent]
    """
    if agent_name not in ["singleAgent","sashaAgent","ourAgent"]:
        raise ValueError("无效的arg：agent_name")

    dir_path = os.path.join(testing_logs_dir, agent_name)
    # 确保目标目录存在（不存在则创建）
    os.makedirs(dir_path, exist_ok=True)

    # 遍历测试用例
    for index, question in enumerate(testcases):
        # if(index+1)>=8:
        #     continue
        init_devices_states()
        # 处理文件名：移除特殊字符，确保文件名合法
        # 保留中文、字母、数字和下划线，其他字符替换为下划线
        cleaned_name = re.sub(r'[^\w\u4e00-\u9fa5]', '', question)
        # 生成文件名：序号_清洗后的内容（如"0_将整个房子变暗"、"1_网络状况"）
        filename = f"{index+1}_{cleaned_name}.log"
        # 生成文件完整路径
        log_file = os.path.join(dir_path, filename)

        # 调用agent
        logger=get_context_logger(log_file=log_file, name=f"{agent_name}_{index}")
        global_config.GLOBAL_AGENT_DETAILED_LOGGER=logger
        logger.info("test")
        try:
            if agent_name=="singleAgent":
                SingleAgent(logger=logger).run_agent(question)
            elif agent_name=="sashaAgent":
                run_sashaAgent(question)
            elif agent_name=="ourAgent":
                SmartHomeAgent().run_agent(question)
        except Exception as e:
            # 1. 获取完整的异常信息（类型、消息、堆栈跟踪）
            # traceback.format_exc() 会返回包含堆栈的字符串，便于调试
            exception_detail = traceback.format_exc()

            # 2. 将异常原样打印到日志（使用error级别，突出异常）
            logger.error(
                f"执行Agent [{agent_name}] 时发生异常：\n"
                f"异常类型：{type(e).__name__}\n"
                f"异常消息：{str(e)}\n"
                f"完整堆栈跟踪：\n{exception_detail}"
            )

            # （可选）若需要向上层传递异常，可取消注释下面一行（根据业务需求决定）
            # raise

def main(agent_name):
    process_testcases(agent_name=agent_name)


if __name__=="__main__":
    main("ourAgent")