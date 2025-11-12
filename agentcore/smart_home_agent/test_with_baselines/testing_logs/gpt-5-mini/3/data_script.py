# 导入需要的模块：os用于处理文件和目录，re用于正则表达式匹配
import os
import re
from openpyxl import Workbook

# 定义需要提取的字段及其对应的正则表达式模式
# 键是字段名称，值是用于匹配该字段的正则表达式（括号部分是要提取的数值）
patterns = {
    '累计输入 token': r"'累计输入 token': (\d+)",  # 匹配整数数字（\d+）
    '累计输出 token': r"'累计输出 token': (\d+)",
    '累计总 token': r"'累计总 token': (\d+)",
    '总运行时间': r"总运行时间：([\d.]+)秒",  # 匹配数字和小数点（如29.49）
    '内存峰值': r"内存峰值：([\d.]+)MB",
    '内存平均值': r"内存平均值：([\d.]+)MB",
    'CPU使用率峰值': r"CPU使用率峰值：([\d.]+)%",
    'CPU使用率平均值': r"CPU使用率平均值：([\d.]+)%"
}

# 定义需要处理的文件夹列表
target_folders = ['singleAgent', 'sashaAgent', 'sageAgent', 'privacyAgent']

# 创建Excel工作簿
wb = Workbook()

# 处理每个目标文件夹
for folder in target_folders:
    # 检查文件夹是否存在
    if not os.path.isdir(folder):
        print(f"警告：文件夹 {folder} 不存在，已跳过")
        continue

    # 初始化结果列表：索引0不用，1-50对应日志文件的序号（1到50）
    results = [{} for _ in range(51)]  # 列表长度51，索引0占位，1-50有效

    # 遍历文件夹下的所有文件
    for filename in os.listdir(folder):
        # 用正则表达式匹配文件名格式："序号_测试用例名.log"
        match = re.match(r'^(\d+)_.*\.log$', filename)
        if not match:  # 如果文件名不匹配格式，跳过该文件
            continue

        # 提取文件名中的序号
        seq = int(match.group(1))
        # 只处理序号1到50的文件，其他序号跳过
        if seq < 1 or seq > 50:
            continue

        # 初始化当前文件的提取结果
        last_occurrences = {key: None for key in patterns}

        # 拼接文件完整路径
        file_path = os.path.join(folder, filename)

        # 打开日志文件，读取内容
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # 对每一行，检查是否包含需要提取的字段
                for key, pattern in patterns.items():
                    m = re.search(pattern, line)
                    if m:
                        # 更新字段值为最后一次出现的值
                        last_occurrences[key] = m.group(1)

        # 保存当前文件的提取结果
        results[seq] = last_occurrences

    # 整理当前文件夹的输出结果
    output = []
    for seq in range(1, 51):
        item = [results[seq][key] for key in patterns]
        output.append(item)

    # 打印当前文件夹的提取结果
    print(f"\n{folder} 提取结果（按序号1-50）：")
    print(
        "顺序：[累计输入token, 累计输出token, 累计总token, 总运行时间(秒), 内存峰值(MB), 内存平均值(MB), CPU峰值(%), CPU平均值(%)]")
    for i, data in enumerate(output, 1):
        print(f"序号{i}: {data}")

    # 创建并配置工作表
    if folder == target_folders[0] and wb.active.title == 'Sheet':
        # 使用默认工作表作为第一个文件夹的工作表
        ws = wb.active
        ws.title = folder
    else:
        # 为其他文件夹创建新工作表
        ws = wb.create_sheet(title=folder)

    # 写入列名（第一行）
    column_names = [
        "累计输入token",
        "累计输出token",
        "累计总token",
        "总运行时间(秒)",
        "内存峰值(MB)",
        "内存平均值(MB)",
        "CPU峰值(%)",
        "CPU平均值(%)"
    ]
    ws.append(column_names)

    # 写入数据
    for row_data in output:
        ws.append(row_data)

# 保存Excel文件
excel_filename = "日志提取结果.xlsx"
wb.save(excel_filename)
print(f"\n所有结果已保存到 {excel_filename}")