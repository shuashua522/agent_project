import re
import ast
from datetime import datetime


def analyze_agent_logs(log_file_path):
    """
    解析agent日志文件，计算每次调用的token总和及执行时长

    参数:
        log_file_path: 日志文件路径

    返回:
        包含每次调用汇总信息的列表
    """
    # 存储所有调用的汇总信息
    all_calls_summary = []

    # 当前调用的汇总数据
    current_call = {
        'input_tokens': 0,
        'output_tokens': 0,
        'total_tokens': 0,
        'reasoning': 0,
        'start_time': None,
        'end_time': None,
        'execution_time': 0,  # 新增：执行时长（秒）
        'task': None
    }

    # 正则表达式匹配消耗token的行
    token_pattern = re.compile(r'消耗的token: ({.*})')
    # 正则表达式匹配执行时长的行
    exec_time_pattern = re.compile(r'agent执行时长: (\d+\.\d+) 秒')

    with open(log_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()

            # 空白行表示一次调用结束
            if not line:
                if current_call['total_tokens'] > 0:  # 确保这是一个有效的调用记录
                    all_calls_summary.append(current_call.copy())
                    # 重置当前调用数据
                    current_call = {
                        'input_tokens': 0,
                        'output_tokens': 0,
                        'total_tokens': 0,
                        'reasoning': 0,
                        'start_time': None,
                        'end_time': None,
                        'execution_time': 0,
                        'task': None
                    }
                continue

            # 提取时间戳
            time_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if time_match:
                timestamp = time_match.group(1)
                if current_call['start_time'] is None:
                    current_call['start_time'] = timestamp
                current_call['end_time'] = timestamp  # 不断更新为最后时间

            # 提取任务描述（通常是每次调用的第一行）
            if 'INFO -' in line and current_call['task'] is None:
                task_part = line.split('INFO - ')[-1]
                if '消耗的token' not in task_part:  # 排除token相关行
                    current_call['task'] = task_part.strip(': ')

            # 查找包含token消耗的行
            token_match = token_pattern.search(line)
            if token_match:
                try:
                    # 解析token字典
                    token_data = ast.literal_eval(token_match.group(1))

                    # 累加token数据
                    current_call['input_tokens'] += token_data.get('input_tokens', 0)
                    current_call['output_tokens'] += token_data.get('output_tokens', 0)
                    current_call['total_tokens'] += token_data.get('total_tokens', 0)

                    # 累加推理token
                    reasoning = token_data.get('output_token_details', {}).get('reasoning', 0)
                    current_call['reasoning'] += reasoning

                except Exception as e:
                    print(f"解析token数据时出错: {e}")
                    print(f"有问题的行: {line}")

            # 提取执行时长
            exec_time_match = exec_time_pattern.search(line)
            if exec_time_match:
                try:
                    current_call['execution_time'] = float(exec_time_match.group(1))
                except Exception as e:
                    print(f"解析执行时长时出错: {e}")
                    print(f"有问题的行: {line}")

    # 检查是否有最后一次未被添加的调用记录
    if current_call['total_tokens'] > 0:
        all_calls_summary.append(current_call)

    return all_calls_summary


def analyze_token_statistics(call_summaries):
    """
    分析汇总后的token信息和执行时长，计算平均值、最大值和最小值

    参数:
        call_summaries: 包含每次调用汇总信息的列表

    返回:
        包含统计信息的字典
    """
    if not call_summaries:
        return None

    # 提取所有调用的各项数据
    input_tokens = [call['input_tokens'] for call in call_summaries]
    output_tokens = [call['output_tokens'] for call in call_summaries]
    total_tokens = [call['total_tokens'] for call in call_summaries]
    reasoning_tokens = [call['reasoning'] for call in call_summaries]
    execution_times = [call['execution_time'] for call in call_summaries]  # 新增：执行时长数据

    # 计算统计值
    stats = {
        'input_tokens': {
            'average': sum(input_tokens) / len(input_tokens),
            'max': max(input_tokens),
            'min': min(input_tokens)
        },
        'output_tokens': {
            'average': sum(output_tokens) / len(output_tokens),
            'max': max(output_tokens),
            'min': min(output_tokens)
        },
        'total_tokens': {
            'average': sum(total_tokens) / len(total_tokens),
            'max': max(total_tokens),
            'min': min(total_tokens)
        },
        'reasoning': {
            'average': sum(reasoning_tokens) / len(reasoning_tokens),
            'max': max(reasoning_tokens),
            'min': min(reasoning_tokens)
        },
        'execution_time': {  # 新增：执行时长统计
            'average': sum(execution_times) / len(execution_times),
            'max': max(execution_times),
            'min': min(execution_times)
        },
        'total_calls': len(call_summaries)
    }

    return stats


# 使用示例
if __name__ == "__main__":
    log_path = "deepseek_agent.log"  # 日志文件路径
    try:
        # 解析日志并获取每次调用的汇总信息
        call_summaries = analyze_agent_logs(log_path)

        print(f"共解析到 {len(call_summaries)} 次agent调用记录\n")

        # 打印每次调用的详细信息
        for i, call in enumerate(call_summaries, 1):
            print(f"第 {i} 次调用:")
            print(f"任务: {call['task']}")
            print(f"时间: {call['start_time']} 至 {call['end_time']}")
            print(f"输入token总和: {call['input_tokens']}")
            print(f"输出token总和: {call['output_tokens']}")
            print(f"总token消耗: {call['total_tokens']}")
            print(f"推理token总和: {call['reasoning']}")
            print(f"执行时长: {call['execution_time']} 秒")  # 新增：显示执行时长
            print("-" * 50)

        # 分析统计数据
        token_stats = analyze_token_statistics(call_summaries)

        if token_stats:
            print("\n===== 统计分析结果 =====")
            print(f"总调用次数: {token_stats['total_calls']}")

            for metric, stats in token_stats.items():
                if metric == 'total_calls':
                    continue
                # 为执行时长添加单位说明
                unit = " 秒" if metric == 'execution_time' else ""
                print(f"\n{metric}:")
                print(f"  平均值: {stats['average']:.2f}{unit}")
                print(f"  最大值: {stats['max']:.2f}{unit}")
                print(f"  最小值: {stats['min']:.2f}{unit}")

    except FileNotFoundError:
        print(f"错误: 找不到日志文件 {log_path}")
    except Exception as e:
        print(f"分析日志时发生错误: {e}")

