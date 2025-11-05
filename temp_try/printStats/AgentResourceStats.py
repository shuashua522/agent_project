import psutil
import time
import threading
from functools import wraps
from dataclasses import dataclass
from typing import List, Callable, Any

@dataclass
class AgentResourceStats:
    """Agent一次运行的资源统计结果"""
    run_time: float  # 总运行时间（秒）
    memory_peak: float  # 内存峰值（MB）
    memory_avg: float  # 内存平均值（MB）
    cpu_peak: float  # CPU使用率峰值（%）
    cpu_avg: float  # CPU使用率平均值（%）

class AgentResourceMonitor:
    def __init__(self, sample_interval: float = 0.1):
        """
        初始化监控器
        :param sample_interval: 采样间隔（秒），越小越精确但开销略高
        """
        self.sample_interval = sample_interval
        self.pid = psutil.Process()  # 当前进程
        self._running = False
        self._memory_samples: List[float] = []  # 内存采样（MB）
        self._cpu_samples: List[float] = []  # CPU采样（%）
        self._start_time: float = 0.0

    def _sample_loop(self):
        """后台采样循环"""
        self._running = True
        # 初始化CPU使用率计算（首次调用返回0，需先触发）
        self.pid.cpu_percent(interval=0.01)
        while self._running:
            # 记录内存（RSS：物理内存，转换为MB）
            mem_rss = self.pid.memory_info().rss / (1024 **2)
            self._memory_samples.append(mem_rss)
            # 记录CPU使用率（基于采样间隔的平均值）
            cpu_percent = self.pid.cpu_percent(interval=self.sample_interval)
            self._cpu_samples.append(cpu_percent)

    def start(self):
        """开始监控"""
        self._start_time = time.time()
        self._memory_samples.clear()
        self._cpu_samples.clear()
        # 启动采样线程（守护线程，随主程序退出）
        self._sample_thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._sample_thread.start()

    def stop(self) -> AgentResourceStats:
        """停止监控并返回统计结果"""
        self._running = False
        self._sample_thread.join()  # 等待采样线程结束
        run_time = time.time() - self._start_time

        # 计算内存指标（过滤空采样的极端情况）
        if self._memory_samples:
            memory_peak = max(self._memory_samples)
            memory_avg = sum(self._memory_samples) / len(self._memory_samples)
        else:
            memory_peak = memory_avg = 0.0

        # 计算CPU指标
        if self._cpu_samples:
            cpu_peak = max(self._cpu_samples)
            cpu_avg = sum(self._cpu_samples) / len(self._cpu_samples)
        else:
            cpu_peak = cpu_avg = 0.0

        return AgentResourceStats(
            run_time=run_time,
            memory_peak=memory_peak,
            memory_avg=memory_avg,
            cpu_peak=cpu_peak,
            cpu_avg=cpu_avg
        )

# 装饰器：用于包装Agent的主函数
def monitor_agent(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        monitor = AgentResourceMonitor(sample_interval=0.1)
        print("开始监控Agent资源使用...")
        monitor.start()
        try:
            # 执行Agent主函数
            result = func(*args, **kwargs)
        finally:
            # 无论Agent是否正常结束，都停止监控并输出结果
            stats = monitor.stop()
            print("\nAgent运行一次的资源统计结果：")
            print(f"总运行时间：{stats.run_time:.2f}秒")
            print(f"内存峰值：{stats.memory_peak:.2f}MB")
            print(f"内存平均值：{stats.memory_avg:.2f}MB")
            print(f"CPU使用率峰值：{stats.cpu_peak:.2f}%")
            print(f"CPU使用率平均值：{stats.cpu_avg:.2f}%")
        return result
    return wrapper

# 你的Agent代码（示例）
def my_agent(task: str):
    """示例Agent：模拟一次任务处理（包含计算和IO）"""
    import time
    import random

    # 模拟内存消耗（创建临时大对象）
    large_data = [random.random() for _ in range(10**6)]
    time.sleep(0.5)  # 模拟IO等待

    # 模拟CPU密集计算
    total = 0
    for i in range(10**7):
        total += i
    time.sleep(0.3)

    # 释放部分内存
    del large_data
    time.sleep(0.2)
    return f"任务 '{task}' 处理完成"

# 用装饰器监控Agent运行一次的资源
@monitor_agent
def run_agent_once():
    return my_agent("用户查询处理")

# 运行并统计
if __name__ == "__main__":
    run_agent_once()