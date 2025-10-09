import os

import requests

from bin.config import set_environment_variables
from sage.coordinators.sage_coordinator import SAGECoordinatorConfig

token=os.getenv("HOMEASSITANT_AUTHORIZATION_TOKEN")
server=os.getenv("HOMEASSITANT_SERVER")
active_project_env=os.getenv("ACTIVE_PROJECT_ENV")
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

def process_testcases(agent_name):
    """
    遍历测试用例
    agent_name取值：[singleAgent,sashaAgent,ourAgent]
    """
    if agent_name not in ["sageAgent"]:
        raise ValueError("无效的arg：agent_name")

    # 遍历测试用例
    for index, question in enumerate(testcases):
        if(index+1)<=10:
            continue
        init_devices_states()
        # 处理文件名：移除特殊字符，确保文件名合法
        # 保留中文、字母、数字和下划线，其他字符替换为下划线

        # 调用agent
        if agent_name=="sageAgent":
            SAGECoordinatorConfig().instantiate().execute(question)


def main(agent_name):
    process_testcases(agent_name=agent_name)


if __name__=="__main__":
    main("sageAgent")