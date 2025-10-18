import os
import re


def extract_last_token_info(file_path):
    """从日志文件最后一行非空白行提取token信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 读取所有行并反转，寻找最后一个非空白行
            for line in reversed(f.readlines()):
                stripped_line = line.strip()
                if stripped_line:
                    # 使用正则表达式提取token数据
                    pattern = r"'累计输入 token': (\d+), '累计输出 token': (\d+), '累计总 token': (\d+)"
                    match = re.search(pattern, stripped_line)
                    if match:
                        return (
                            int(match.group(1)),  # 累计输入token
                            int(match.group(2)),  # 累计输出token
                            int(match.group(3))  # 累计总token
                        )
                    return None
        return None
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
        return None


def main():
    # 获取当前目录下所有符合命名规则的log文件
    log_files = []
    file_pattern = re.compile(r'^(\d+)_.*\.log$')

    for filename in os.listdir('.'):
        match = file_pattern.match(filename)
        if match:
            try:
                # 提取文件序号并存储
                seq_number = int(match.group(1))
                log_files.append((seq_number, filename))
            except ValueError:
                continue

    # 按文件序号排序
    log_files.sort(key=lambda x: x[0])

    # 提取各类型token信息
    input_tokens = []
    output_tokens = []
    total_tokens = []

    for seq, filename in log_files:
        token_info = extract_last_token_info(filename)
        if token_info:
            input_t, output_t, total_t = token_info
            input_tokens.append(input_t)
            output_tokens.append(output_t)
            total_tokens.append(total_t)
        else:
            print(f"警告：无法从 {filename} 中提取token信息")
            input_tokens.append(None)
            output_tokens.append(None)
            total_tokens.append(None)

    # 输出结果
    print(f"累计输入 token 消耗列表（按文件序号）: {input_tokens}")
    print(f"累计输出 token 消耗列表（按文件序号）: {output_tokens}")
    print(f"累计总 token 消耗列表（按文件序号）: {total_tokens}")


if __name__ == "__main__":
    main()