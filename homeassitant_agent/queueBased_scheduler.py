import inspect
import time
import threading
import uuid
from queue import Queue, Empty
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
from uuid import uuid4

from apscheduler.triggers.cron import CronTrigger


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
        self.worker_thread = threading.Thread(target=self.process_tasks, daemon=True)
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

    def add_cron_task_to_queue(
            self,
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

        self.add_task_to_queue(task)

    def add_conditional_task_to_queue(
            self,
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

        global_namespace = {}
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

        self.add_task_to_queue(task)
    def add_interval_task_to_queue(self,
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

        self.add_task_to_queue(task)

    def call_agent_do(self,statement):
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
                print("队列暂时无任务，继续等待...")
                continue  # 跳过本次循环，继续等待新任务
            except Exception as e:
                if not self.running:
                    break
                print(f"处理任务出错: 类型={type(e)}, 信息={str(e)}")


# ---------------------- 示例使用 ----------------------
if __name__ == "__main__":
    global_condition = {
        "task1": False,
    }

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
        func_str = "def check_condition1():return True"
        scheduler.add_conditional_task_to_queue("条件任务1：当条件满足时执行目标动作",
                                                "执行条件任务1的目标动作，输出指定信息", func_str, "check_condition1", {
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


# 验证参数合法性（必须是非负数字）
#     valid_keys = {'weeks', 'days', 'hours', 'minutes', 'seconds', 'microseconds'}
#     for key, value in interval_params.items():
#         if key not in valid_keys:
#             raise ValueError(f"无效的时间参数：{key}，支持的参数：{valid_keys}")
#         if not isinstance(value, (int, float)) or value < 0:
#             raise ValueError(f"参数 {key} 的值必须是非负数字，当前值：{value}")