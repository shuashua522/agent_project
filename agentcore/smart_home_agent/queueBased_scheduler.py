import inspect
import json
import os
import time
import threading
import uuid
from queue import Queue, Empty
from typing import Callable, List, Dict, Union, Annotated

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
from uuid import uuid4

from apscheduler.triggers.cron import CronTrigger
from langchain_core.tools import tool
from langgraph.graph import MessagesState

from agent_project.agentcore.commons.base_agent import BaseToolAgent
from agent_project.agentcore.commons.utils import get_llm
from typing import Optional

################################################
# 模拟数据的文件所在目录
mock_data_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),  # 当前文件所在目录
    'test_mock_data'  # 子目录（无开头斜杠）
)
def extract_entity_by_id(json_file_path: str, target_entity_id: str) -> Optional[Dict]:
    """
    从指定JSON文件中提取目标entity_id对应的字典数据

    参数:
        json_file_path: JSON文件的完整路径（如"D:/homeassistant/entities.json"）
        target_entity_id: 要提取的实体ID（如"sun.sun"、"person.shua"）

    返回:
        若找到目标entity_id，返回对应的字典；若未找到或出现异常，返回None
    """
    # 初始化结果为None，默认未找到目标
    target_entity: Optional[Dict] = None

    # 1. 读取JSON文件内容
    with open(json_file_path, 'r', encoding='utf-8') as f:
        # 2. 解析JSON数据，转换为Python列表（数据结构为List[Dict]）
        entity_list: List[Dict] = json.load(f)

        # 3. 验证解析后的数据是否为列表（防止JSON文件格式错误）
        if not isinstance(entity_list, list):
            print(f"错误：JSON文件内容不是列表格式，实际类型为{type(entity_list).__name__}")
            return None

        # 4. 遍历列表，匹配目标entity_id
        for entity in entity_list:
            # 检查当前字典是否包含"entity_id"键（防止数据不完整）
            if "entity_id" not in entity:
                print(f"警告：跳过无效数据，该字典缺少'entity_id'键：{entity}")
                continue

            # 匹配到目标entity_id，记录结果并退出循环
            if entity["entity_id"] == target_entity_id:
                target_entity = entity
                break
    return target_entity
def get_all_entity_id()-> Union[Dict, List]:
    """
    Returns an array of state objects.
    Each state has the following attributes: entity_id, state, last_changed and attributes.
    """
    # headers = {
    #     "Authorization": f"Bearer {token}",
    #     "Content-Type": "application/json"
    # }
    #
    # url = "http://localhost:8123/api/states"
    #
    # # 发送GET请求
    # response = requests.get(url, headers=headers)
    # # 检查请求是否成功
    # response.raise_for_status()
    # # 返回JSON响应内容
    # return response.json()
    file_path=os.path.join(mock_data_dir, 'selected_entities.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        # 解析JSON文件并返回Python对象
        return json.load(f)
def get_states_by_entity_id(entity_id: Annotated[str, "查看{entity_id}的状态"],) -> Union[Dict, List]:
    """
    Returns a state object for specified entity_id.
    Returns 404 if not found.
    """
    file_path = os.path.join(mock_data_dir, 'selected_entities.json')
    return extract_entity_by_id(file_path,entity_id)

    # headers = {
    #     "Authorization": f"Bearer {token}",
    #     "Content-Type": "application/json"
    # }
    #
    # url = f"http://localhost:8123/api/states/{entity_id}"
    #
    # # 发送GET请求
    # response = requests.get(url, headers=headers)
    # # 检查请求是否成功
    # response.raise_for_status()
    # # 返回JSON响应内容
    # return response.json()
################################################


class QueueBasedScheduler:
    def __init__(self):
        self.task_queue = Queue()
        self.scheduler = BackgroundScheduler()
        self.running = False
        self.worker_thread = None
        # 存储条件任务的状态检查器
        self.condition_checkers = {}  # {task_id: 条件检查函数}

    def start(self):
        self.running = True
        self.scheduler.start()
        self.worker_thread = threading.Thread(
            target=self.process_tasks,
            daemon=True,
            name="task_queue_to_scheduler_worker"  # 线程名：体现“队列任务→调度器”的功能
        )
        self.worker_thread.start()
        print("调度器已启动，等待接收任务...")

    def stop(self):
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
        self.scheduler.shutdown()
        print("调度器已停止")

    # 外部与调度交互入口
    def add_task_to_queue(self, task)->None:
        """添加任务到队列，支持interval, cron, conditional三种类型

        """
        print(task)

        if task["task_type"] == 'conditional':
            # 从传入的参数中获取名为condition_func的条件检查函数
            condition_func = task['task_args']["condition_func"]
            # 验证：如果没提供这个函数，或者提供的不是可调用的（比如不是函数）
            if not condition_func or not callable(condition_func):
                # 抛出错误，要求必须提供有效的条件检查函数
                raise ValueError("条件任务必须提供可调用的condition_func参数")

            # 把条件检查函数存入字典，用任务ID作为key（方便后续查找）
            self.condition_checkers[task["task_id"]] = condition_func

        self.task_queue.put(task)

    def call_agent_do(self,statement):
        # TODO 待实现
        print(f"call_agent_do:  {statement}\n")

    def process_tasks(self):
        """从队列获取任务并添加到调度器"""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                task_id = task['task_id']
                task_type = task['task_type']
                action_statement=task["action_statement"]

                if task_type == 'interval':
                    self.scheduler.add_job(
                        func=self.call_agent_do,
                        trigger='interval',
                        args=(action_statement,),
                        id=task_id,
                        ** task["task_args"]["interval_setting"]
                    )

                elif task_type == 'cron':
                    self.scheduler.add_job(
                        func=self.call_agent_do,
                        trigger=task["task_args"]["cronTrigger"],
                        args=(action_statement,),
                        id=task_id
                    )

                elif task_type == 'conditional':
                    # 条件任务的包装函数，负责检查条件并决定是否终止
                    def conditional_wrapper(*args, **kwargs):
                        job: Job = kwargs.get('job')
                        if not job:
                            return

                        # 获取该任务的条件检查函数
                        condition_func = self.condition_checkers.get(job.id)
                        if not condition_func:
                            job.remove()
                            return

                        # 检查条件是否满足
                        if condition_func():
                            # 条件满足，执行目标函数
                            self.call_agent_do(*args)
                            # 移除任务，不再执行
                            job.remove()
                            # 清理条件检查器
                            if job.id in self.condition_checkers:
                                del self.condition_checkers[job.id]
                            print(f"条件任务 {job.id} 满足条件，执行后终止")
                        # 条件不满足，等待下一次检查

                    self.scheduler.add_job(
                        func=conditional_wrapper,
                        trigger='interval',
                        args=(action_statement,),
                        id=task_id,
                        **task["task_args"]["interval_setting"],
                        kwargs={'job': None}  # 占位，实际会被替换为当前job对象
                    )

                    # 获取刚添加的任务，补充job参数
                    job = self.scheduler.get_job(task_id)
                    if job:
                        job.modify(kwargs={'job': job})

                self.task_queue.task_done()

                # 单独捕获队列超时异常（非错误）
            except Empty:
                # 可选：仅在调试时打印，正常运行时可注释
                # print("队列暂时无任务，继续等待...")
                continue  # 跳过本次循环，继续等待新任务
            except Exception as e:
                if not self.running:
                    break
                print(f"处理任务出错: 类型={type(e)}, 信息={str(e)}")

queueBasedScheduler=QueueBasedScheduler()
queueBasedScheduler.start()

@tool
def add_cron_task_to_queue(
        task_desc: str,
        action_statement: str,
        **kwargs
) -> None:
    """
    创建基于Cron表达式的定时任务并添加到任务队列（无返回值）

    该方法通过接收CronTrigger所需的关键字参数动态构建触发器，
    生成标准化任务字典后，自动调用`add_task_to_queue()`方法将任务
    加入队列，完成定时任务的注册流程。执行成功后无返回值，专注于
    任务入队操作本身。

    :param task_desc: 任务描述信息，用于说明任务的用途和目标
    :type task_desc: str
    :param action_statement: 任务执行的具体操作说明，描述需要执行的动作
    :type action_statement: str
    :param**kwargs: 传递给CronTrigger的关键字参数，具体规则如下：
        - year: 4位年份，支持通配符(*)、范围(-)、列表(,)、步长(*/n)
                示例："2024"（2024年）、"2024-2026"（2024-2026年）、"*/2"（偶数年）
        - month: 月份(1-12)，支持通配符和别名（jan-dec）
                示例："3"（3月）、"3,6,9"（3/6/9月）、"1-6"（1-6月）
        - day: 日期(1-31)，支持通配符和L（当月最后一天）
                示例："1"（每月1日）、"1-10"（每月1-10日）、"L"（每月最后一天）
        - week: ISO周数(1-53)，支持通配符
                示例："5"（第5周）、"1-10"（前10周）
        - day_of_week: 星期(0-6或mon-sun，0/mon为周一)，支持通配符和别名
                示例："1"（周一）、"1-5"（周一至周五）、"sat,sun"（周六日）
        - hour: 小时(0-23)，支持通配符和步长
                示例："8"（8点）、"8-17"（8-17点）、"*/2"（每2小时）
        - minute: 分钟(0-59)，支持通配符和步长
                示例："30"（30分）、"0,30"（0分和30分）、"*/15"（每15分钟）
        - second: 秒(0-59)，支持通配符和步长
                示例："0"（0秒）、"*/3"（每3秒）、"10-20/5"（10-20秒每5秒）
        - start_date: 最早触发时间（包含），格式为datetime对象或字符串
                示例："2024-01-01 08:00:00"、datetime(2024, 1, 1)
        - end_date: 最晚触发时间（包含），格式同start_date
                示例："2024-12-31 23:59:59"
        - timezone: 时区，支持tzinfo对象或时区字符串
                示例："Asia/Shanghai"（中国标准时间）、"UTC"
        - jitter: 最大延迟秒数（随机延迟0-jitter秒执行），避免并发
                示例：10（最多延迟10秒）
    :type **kwargs: Any
    :rtype: None
    :raises ValueError: 当参数格式无效或触发器创建失败时触发
    :raises Exception: 当调用`add_task_to_queue()`添加任务到队列失败时可能触发，
                       具体异常类型取决于`add_task_to_queue()`的实现

    :示例:
        >>> add_cron_task_to_queue(
        ...     task_desc="工作日早会提醒",
        ...     action_statement="发送早会通知到企业微信",
        ...     hour=8,
        ...     minute=30,
        ...     second=0,
        ...     day_of_week="1-5",
        ...     start_date="2024-01-01",
        ...     timezone="Asia/Shanghai",
        ...     jitter=30
        ... )
        # 执行成功后无返回值，任务已添加到队列
    """
    # 验证并创建CronTrigger触发器
    try:
        trigger = CronTrigger(**kwargs)
    except TypeError as e:
        raise ValueError(f"CronTrigger参数错误: {str(e)}") from e
    except Exception as e:
        raise ValueError(f"创建触发器失败: {str(e)}") from e

    # 生成唯一任务ID
    task_id = str(uuid.uuid4())

    # 构建标准化任务字典
    task = {
        "task_type": "cron",
        "task_id": task_id,
        "task_desc": task_desc,
        "action_statement": action_statement,
        "task_args": {
            "cronTrigger": trigger  # 存储CronTrigger实例用于调度
        }
    }

    queueBasedScheduler.add_task_to_queue(task)


@tool
def add_conditional_task_to_queue(
        task_desc: str,
        action_statement: str,
        condition_func_code: str,
        condition_func_name: str,
        interval_setting: dict,
) -> None:
    """
    创建基于条件触发的任务并添加到任务队列

    该方法通过执行字符串形式的条件函数代码，构建条件触发型任务。系统会根据
    配置的时间间隔定期执行条件函数，当函数返回True时触发任务执行。任务生成后
    自动添加到队列中，无返回值。

    :param task_desc: 任务描述信息，用于说明条件任务的用途和目标
    :type task_desc: str
    :param action_statement: 任务满足条件后执行的具体操作说明
    :type action_statement: str
    :param condition_func_code: 条件检查函数的完整代码字符串，需定义一个返回布尔值的函数
                               函数返回True表示满足条件（触发任务），返回False表示不满足
                               示例："def check_temp():\n    return get_current() > 30"
    :type condition_func_code: str
    :param condition_func_name: 条件检查函数在代码字符串中定义的函数名，用于从命名空间中获取函数
                               必须与condition_func_code中定义的函数名完全一致
                               示例：若代码定义def check_temp()，则此处传"check_temp"
    :type condition_func_name: str
    :param interval_setting: 条件检查间隔配置字典，支持以下时间维度的组合：
                             - weeks: 周数（int）
                             - days: 天数（int）
                             - hours: 小时数（int）
                             - minutes: 分钟数（int）
                             - seconds: 秒数（int）
                             - microseconds: 微秒数（int）
                             示例：{"minutes": 5, "seconds": 30} 表示每5分30秒检查一次
    :type interval_setting: dict
    :rtype: None
    :示例:
        >>> # 定义条件函数代码字符串和函数名
        >>> func_code = '''
        ... def check_temperature():
        ...     current_temp = get_sensor_data("temp_sensor")  # 假设的传感器数据获取函数
        ...     return current_temp > 30  # 温度超过30℃返回True
        ... '''
        >>> func_name = "check_temperature"
        >>>
        >>> # 添加条件任务
        >>> scheduler.add_conditional_task_to_queue(
        ...     task_desc="温度超标警报",
        ...     action_statement="发送温度超标短信通知管理员",
        ...     condition_func_code=func_code,
        ...     condition_func_name=func_name,
        ...     interval_setting={"seconds": 10}  # 每10秒检查一次
        ... )
    """
    # 验证检查间隔配置（至少包含一个有效时间维度）
    valid_interval_keys = {"weeks", "days", "hours", "minutes", "seconds", "microseconds"}
    interval_keys = set(interval_setting.keys())
    if not interval_keys.issubset(valid_interval_keys):
        invalid_keys = interval_keys - valid_interval_keys
        raise ValueError(f"interval_setting 包含无效键：{invalid_keys}，仅支持：{valid_interval_keys}")
    if not interval_setting:  # 空字典无意义
        raise ValueError("interval_setting 不能为空，请至少配置一个时间维度（如 seconds: 1）")

    global_namespace = {
        # 将外部导入的函数添加到命名空间
        'get_states_by_entity_id': get_states_by_entity_id,
        'get_all_entity_id': get_all_entity_id
    }
    # 执行函数代码字符串
    exec(condition_func_code, global_namespace)

    # 从命名空间中获取函数
    if condition_func_name in global_namespace:
        condition_func = global_namespace[condition_func_name]
    else:
        raise ValueError(f"条件函数名 '{condition_func_name}' 未在代码字符串中定义，请检查函数名是否匹配")

    task_id = str(uuid.uuid4())

    task = {
        "task_type": "conditional",  # 任务类型：条件触发型
        "task_id": task_id,
        "task_desc": task_desc,
        "action_statement": action_statement,
        "task_args": {
            "condition_func": condition_func,
            "interval_setting": interval_setting,
        }
    }

    queueBasedScheduler.add_task_to_queue(task)


@tool
def add_interval_task_to_queue(
       task_desc: str,
       action_statement: str,
       interval_setting: dict,
) -> None:
    """
    创建基于固定间隔的定时任务并添加到任务队列

    该方法用于构建固定间隔执行的任务，根据指定的时间间隔配置（如每5分钟、每2小时等）
    定期触发任务执行。任务生成后自动添加到队列中，无返回值。

    :param task_desc: 任务描述信息，说明该间隔任务的用途和目标
    :type task_desc: str
    :param action_statement: 任务执行的具体操作说明，描述每次间隔触发时需要执行的动作
    :type action_statement: str
    :param interval_setting: 任务执行的时间间隔配置字典，支持以下时间维度的组合（键名固定）：
                             - weeks: 周数（int），例如：{"weeks": 1} 表示每1周
                             - days: 天数（int），例如：{"days": 2} 表示每2天
                             - hours: 小时数（int），例如：{"hours": 3} 表示每3小时
                             - minutes: 分钟数（int），例如：{"minutes": 30} 表示每30分钟
                             - seconds: 秒数（int），例如：{"seconds": 10} 表示每10秒
                             - microseconds: 微秒数（int），通常用于高精度间隔
                             示例：{"hours": 1, "minutes": 30} 表示每1小时30分钟执行一次
    :type interval_setting: dict
    :rtype: None

    :示例:
        >>> # 添加每30分钟执行一次的日志备份任务
        >>> scheduler.add_interval_task_to_queue(
        ...     task_desc="系统日志定期备份",
        ...     action_statement="压缩并归档/var/log目录下的日志文件至备份服务器",
        ...     interval_setting={"minutes": 30}
        ... )
    """

    task_id = str(uuid.uuid4())
    task = {
        "task_type": "interval",
        "task_id": task_id,
        "task_desc": task_desc,
        "action_statement": action_statement,
        "task_args": {
            "interval_setting": interval_setting,
        }
    }

    queueBasedScheduler.add_task_to_queue(task)

class GenerateTaskToQueueAgent(BaseToolAgent):

    def get_tools(self) -> List[Callable]:
        tools=[add_conditional_task_to_queue,
               add_cron_task_to_queue,
               add_interval_task_to_queue]
        return tools

    def call_tools(self, state: MessagesState):
        system_prompt = """
            根据用户提供的任务，选用恰当的工具将其添加到任务队列中。
            注意：如果工具没有返回值，只要其不报错，即可视为其成功将其加入到任务队列中
        """
        llm = get_llm().bind_tools(self.get_tools())
        system_message = {
            "role": "system",
            "content": system_prompt,
        }
        response = llm.invoke([system_message] + state["messages"])
        return {"messages": [response]}

@tool
def generateTaskToQueueTool(
    task_desc: str,
    action_statement: str,
    condition_func_code: Optional[str]=None,
    condition_func_name: Optional[str]=None,
    time_ruler: str = "每2秒执行一次"
) -> str:
    """将“任务加入队列”，并持续监控，当条件或者时间满足时，会自动执行任务。
    用于定义带时间规则、条件判断的任务。

    :param task_desc: 用一句话描述本次任务的核心目标（如“定时获取网络状况”）
    :type task_desc: str
    :param action_statement: 自然语言描述的任务执行动作，格式为：当时间规则{time_ruler}满足时，执行本参数描述的操作（如“调用设备数据采集接口”）
    :type action_statement: str
    :param condition_func_code: 条件判断函数的Python代码字符串（可为空）。非空时需返回布尔值，用于控制{action_statement}是否执行
    :type condition_func_code: Optional[str]
    :param condition_func_name: 条件函数的名称（可为空）。当{condition_func_code}非空时，需与函数定义中的名称一致
    :type condition_func_name: Optional[str]
    :param time_ruler: 自然语言描述的时间规则，定义执行或检查条件的时机，默认“每2秒执行一次”
    :type time_ruler: str
    :return: 执行任务入队后的结果字符串
    :rtype: str
    """
    # 收集所有参数到字典
    params_dict = {
        "task_desc": task_desc,
        "action_statement": action_statement,
        "condition_func_code": condition_func_code,
        "condition_func_name": condition_func_name,
        "time_ruler": time_ruler
    }

    # 过滤掉值为None或空字符串的键
    filtered_params = {
        key: value for key, value in params_dict.items()
        if value is not None and value != ""
    }
    problem = json.dumps(filtered_params, ensure_ascii=False)

    return GenerateTaskToQueueAgent().run_agent(problem)

# ---------------------- 示例使用 ----------------------
if __name__ == "__main__":
    # print("hi")
    # try:
    #     # scheduler.add_interval_task_to_queue("系统状态监控：每30分钟检查一次服务器资源使用情况","采集CPU、内存、磁盘使用率，超出阈值时发送告警",{
    #     #             "seconds": 2  # 检查间隔设置为1秒，对应原check_interval=1
    #     #         })
    #     # scheduler.add_cron_task_to_queue("高频数据采集：工作日每5分钟采集一次传感器数据","读取车间温度、湿度传感器数据，存入时序数据库",second="*/3",  # 秒：每3秒
    #     #     minute="*",  # 分：任意
    #     #     hour="*",  # 时：任意
    #     #     day="*",  # 日：任意
    #     #     month="*",  # 月：任意
    #     #     day_of_week=None  )
    #     # func_str = "def check_condition1():return True"
    #     condition_func_code = "def func() -> bool:\n    try:\n        # 获取光照度传感器的状态\n        light_state = get_states_by_entity_id(entity_id=\"sensor.isa_cn_blt_3_1md0u6qht0k00_dw2hl_illumination_p_2_1\")\n        # 检查状态是否为\"强\"（表示光照充足）\n        return light_state[\"state\"] == \"强\"\n    except Exception as e:\n        # 处理异常情况（如传感器未找到、状态获取失败等），此时认为光照不充足\n        print(f\"获取光照状态失败: {e}\")\n        return False",
    #     add_conditional("条件任务1：当条件满足时执行目标动作",
    #                                             "执行条件任务1的目标动作，输出指定信息", condition_func_code, "func", {
    #                                                 "seconds": 1  # 检查间隔设置为1秒，对应原check_interval=1
    #                                             })
    #
    #     # 保持主线程运行
    #     while True:
    #         time.sleep(1)
    #
    # except KeyboardInterrupt:
    #     print("\n收到停止信号")
    # finally:
    #     queueBasedScheduler.stop()
    pass

