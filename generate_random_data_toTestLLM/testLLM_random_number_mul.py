import random
import os
import threading

from langchain.chat_models import init_chat_model
import configparser
import logging
import time

from agent_project.utils.qq_email_sender import send_email_to_self


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

def get_llm(provider):
    # 创建配置解析器对象
    config = configparser.ConfigParser()
    # 读取INI文件
    config.read('my_config.ini', encoding='utf-8')
    # 设置LangSmith跟踪开关和API密钥
    os.environ["LANGSMITH_TRACING"] = config.get('LangSmith', 'langsmith_tracing')
    os.environ["LANGSMITH_API_KEY"] = config.get('LangSmith', 'langsmith_api_key')

    # provider = "doubao"
    model = config.get(provider, 'model')
    base_url = config.get(provider, 'base_url')
    api_key = config.get(provider, 'api_key')

    llm = None
    if (provider == "openai"):
        proxies = {
            'http': 'http://127.0.0.1:33210',  # HTTP 请求使用 33210 端口的 HTTP 代理
            'https': 'http://127.0.0.1:33210',  # HTTPS 请求使用 33210 端口的 HTTP 代理
        }
        import httpx
        httpx_client = httpx.Client()
        httpx_client.proxies = proxies

        llm = init_chat_model(
            model=model,
            model_provider="openai",
            api_key=api_key,
            base_url=base_url,
            temperature=0,
            http_client=httpx_client
        )
    else:
        llm = init_chat_model(
            model=model,
            model_provider="openai",
            api_key=api_key,
            base_url=base_url,
            temperature=0,
        )
    return llm

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

def llm_func(n,provider,logger):
    logger.info(f"取随机{n}个数相乘: ")

    numbers=[random.randint(2, 9) for _ in range(n)]
    logger.info(f"生成的随机数字列表: {numbers}")

    std_answer=get_std_answer(numbers)
    logger.info(f"这{n}个数字相乘的正确答案: {std_answer}")

    llm=get_llm(provider)
    problem=generate_problem(numbers)

    user_message = {
        "role": "user",
        "content": problem,
    }
    # 调用模型检查
    start_time = time.perf_counter()  # 记录开始时间（高精度）
    response = llm.invoke([user_message])
    end_time = time.perf_counter()  # 记录结束时间

    llm_answer = response.content
    logger.info(f"llm计算的结果: {llm_answer}")

    token_usage=response.usage_metadata
    logger.info(f"llm消耗的token情况: {token_usage}")

    logger.info(f"llm执行时长: {end_time - start_time:.3f} 秒\n")

def main_for_llm():
    # providers = ["doubao", "deepseek"]
    providers = ["deepseek"]
    # problem_len = [38, 42]
    problem_len = [47]

    """创建并运行指定数量的线程"""
    threads = []

    # 创建线程
    for i in range(len(providers)):
        # 循环使用提供商列表中的值
        provider = providers[i]
        logger = setup_file_logger(f"{provider}_llm.log")
        # 创建线程，传递参数
        thread = threading.Thread(
            target=llm_func,
            args=(problem_len[i], provider, logger)
        )
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    try:
        main_for_llm()
        send_email_to_self("代码运行完毕")
    except Exception as e:
        send_email_to_self("代码出错！！！")
