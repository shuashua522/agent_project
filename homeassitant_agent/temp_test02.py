# 示例条件变量（实际应用中可能是数据库状态、文件内容等）
import threading
import time
import uuid

from apscheduler.triggers.cron import CronTrigger

from agent_project.homeassitant_agent.temp_test import QueueBasedScheduler

global_condition = {
    "task1": False,
}

# 示例条件检查函数
def check_condition1():
    return global_condition["task1"]

# 创建调度器
scheduler = QueueBasedScheduler()
scheduler.start()

try:
    # scheduler.add_interval_task_to_queue("系统状态监控：每30分钟检查一次服务器资源使用情况","采集CPU、内存、磁盘使用率，超出阈值时发送告警",{
    #             "seconds": 2  # 检查间隔设置为1秒，对应原check_interval=1
    #         })
    # scheduler.add_cron_task_to_queue("高频数据采集：工作日每5分钟采集一次传感器数据","读取车间温度、湿度传感器数据，存入时序数据库",second="*/3",  # 秒：每3秒
    #     minute="*",  # 分：任意
    #     hour="*",  # 时：任意
    #     day="*",  # 日：任意
    #     month="*",  # 月：任意
    #     day_of_week=None  )
    func_str="def check_condition1():return True"
    scheduler.add_conditional_task_to_queue("条件任务1：当条件满足时执行目标动作","执行条件任务1的目标动作，输出指定信息",func_str,"check_condition1",{
                "seconds": 1  # 检查间隔设置为1秒，对应原check_interval=1
            })


    # 主线程：模拟5秒后满足任务1的条件，10秒后满足任务2的条件
    def simulate_conditions():
        time.sleep(5)
        print("\n模拟条件1满足")
        global_condition["task1"] = True


    # 启动条件模拟线程
    threading.Thread(target=simulate_conditions, daemon=True).start()

    # 保持主线程运行
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n收到停止信号")
finally:
    scheduler.stop()