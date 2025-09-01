import random
import os
import threading

from langchain.chat_models import init_chat_model
import configparser
import logging
import time

from agent_project.agent_new import MyAgent
from agent_project.utils.wy163_email_sender import send_email_to_self


def setup_file_logger(log_file, level=logging.INFO):
    """
    配置日志记录器，将日志写入指定文件，编码为UTF-8

    参数:
        log_file: 日志文件路径
        level: 日志级别，默认INFO
    """
    # 创建日志记录器
    logger_name = f"Logger_{log_file}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 创建文件处理器，指定UTF-8编码
    file_handler = logging.FileHandler(log_file, encoding='utf-8')

    # 定义日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # 添加处理器到日志记录器
    logger.addHandler(file_handler)

    return logger

def get_std_answer(numbers):
    """
    计算列表中所有数字相乘的结果

    参数:
        numbers: 包含数字的列表

    返回:
        列表中所有数字的乘积，如果列表为空则返回1
    """
    # 初始化乘积为1（乘法的单位元）
    product = 1

    # 遍历列表中的每个数字并相乘
    for num in numbers:
        product *= num

    return product

def generate_problem(numbers):
    problem='*'.join(map(str, numbers))
    return f"计算：{problem}。直接给出答案，无需过程。"

def agent_func(n,provider,logger):
    logger.info(f"取随机{n}个数相乘: ")

    numbers=[random.randint(2, 9) for _ in range(n)]
    logger.info(f"生成的随机数字列表: {numbers}")

    std_answer=get_std_answer(numbers)
    logger.info(f"这{n}个数字相乘的正确答案: {std_answer}")

    problem = generate_problem(numbers)

    start_time = time.perf_counter()  # 记录开始时间（高精度）
    agent_answer = MyAgent(provider, logger).get_answer_ByAgent(problem)
    end_time = time.perf_counter()  # 记录结束时间

    logger.info(f"agent计算的结果: {agent_answer.strip()}")
    logger.info(f"agent执行时长: {end_time - start_time:.3f} 秒\n")

def main_for_agent():
    providers = ["doubao", "deepseek"]
    problem_len = [47, 47]

    """创建并运行指定数量的线程"""
    threads = []

    # 创建线程
    for i in range(len(providers)):
        # 循环使用提供商列表中的值
        provider = providers[i]
        logger = setup_file_logger(f"{provider}_agent.log")
        # 创建线程，传递参数
        thread = threading.Thread(
            target=agent_func,
            args=(problem_len[i], provider, logger)
        )
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    try:
        main_for_agent()
        send_email_to_self("代码运行完毕")
    except Exception as e:
        send_email_to_self("代码出错！！！")
