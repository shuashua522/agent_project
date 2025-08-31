import logging
import os
import threading
from random import random


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

def llm_func(logger):
    logger.info(f"hi")
providers = ["doubao", "deepseek"]
problem_len = [30, 30]

"""创建并运行指定数量的线程"""
threads = []
"""创建并运行指定数量的线程"""
threads = []

# 创建线程
for i in range(2):
    # 循环使用提供商列表中的值
    provider = providers[i]
    logger = setup_file_logger(f"{provider}_llm.log")
    # 创建线程，传递参数
    thread = threading.Thread(
        target=llm_func,
        args=(logger,)
    )
    threads.append(thread)
    thread.start()

# 等待所有线程完成
for thread in threads:
    thread.join()