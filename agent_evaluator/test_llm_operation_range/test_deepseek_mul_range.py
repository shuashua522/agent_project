import logging
import os
import configparser
from langchain.chat_models import init_chat_model

def setup_logger():
    # 创建mul目录（如果不存在）
    log_dir = "mul"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 日志文件路径
    log_file = os.path.join(log_dir, "deepseek-base7.txt")

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,  # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
        format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
        datefmt='%Y-%m-%d %H:%M:%S',  # 时间格式
        filename=log_file,  # 日志文件
        filemode='a'  # 写入模式：a追加，w覆盖
    )

    return logging.getLogger(__name__)
def std_func(base,exp):
    return base**exp
def get_llm():
    # 创建配置解析器对象
    config = configparser.ConfigParser()
    # 读取INI文件
    config.read('my_config.ini', encoding='utf-8')
    # 设置LangSmith跟踪开关和API密钥
    os.environ["LANGSMITH_TRACING"] = config.get('LangSmith', 'langsmith_tracing')
    os.environ["LANGSMITH_API_KEY"] = config.get('LangSmith', 'langsmith_api_key')

    provider = "deepseek"
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
import utils
def llm_func(base,exp):
    llm=get_llm()
    # problem=f"计算：{base}的{exp}次方。直接给出结果"
    problem = "直接给出结果：" + utils.power_to_multiplication_str(base, exp)
    user_message = {
        "role": "user",
        "content": problem,
    }
    # 调用模型检查
    response = llm.invoke([user_message])
    return response.content

if __name__ == "__main__":
    # 初始化日志
    logger = setup_logger()

    try:
        # 示例计算：7的3次方
        base = 7
        exp = 34
        result = std_func(base,exp)
        logger.info(f"{base}的{exp}次方结果是：{result}")
        result = llm_func(base,exp)
        logger.info(f"llm的回答是：{result}\n")
    except Exception as e:
        logger.error(f"计算过程出错：{str(e)}")

