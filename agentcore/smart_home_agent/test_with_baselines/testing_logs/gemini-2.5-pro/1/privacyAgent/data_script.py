# 导入需要的模块：os用于处理文件和目录，re用于正则表达式匹配
import os
import re

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

# 初始化结果列表：索引0不用，1-50对应日志文件的序号（1到50）
# 每个元素是一个字典，用于存储该序号文件的所有提取结果
results = [{} for _ in range(51)]  # 列表长度51，索引0占位，1-50有效

# 遍历当前目录下的所有文件
for filename in os.listdir('.'):  # os.listdir('.')获取当前目录所有文件名

    # 用正则表达式匹配文件名格式："序号_测试用例名.log"
    # ^(\d+)_：以数字（序号）开头，后面跟下划线
    # .*\.log$：中间是任意字符，最后以.log结尾
    match = re.match(r'^(\d+)_.*\.log$', filename)
    if not match:  # 如果文件名不匹配格式，跳过该文件
        continue

    # 提取文件名中的序号（如"3_网络状况.log"提取出"3"，转换为整数3）
    seq = int(match.group(1))
    # 只处理序号1到50的文件，其他序号跳过
    if seq < 1 or seq > 50:
        continue

    # 初始化当前文件的提取结果：所有字段先设为None（默认无数据）
    last_occurrences = {key: None for key in patterns}

    # 打开日志文件，读取内容（忽略编码错误，避免文件编码问题导致报错）
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        # 逐行读取文件内容（因为要找"最后一次出现"的信息，必须按顺序读）
        for line in f:
            # 对每一行，检查是否包含需要提取的字段
            for key, pattern in patterns.items():
                # 用正则表达式在当前行中搜索字段
                m = re.search(pattern, line)
                if m:  # 如果匹配到（该行包含该字段）
                    # 更新字段值为提取到的数值（覆盖之前的值，最终保留最后一次出现的值）
                    last_occurrences[key] = m.group(1)  # group(1)是正则表达式中括号里的内容

    # 将当前文件的提取结果存入results列表对应序号的位置
    results[seq] = last_occurrences

# 整理最终输出：按序号1到50的顺序，把每个文件的结果转为列表
output = []
for seq in range(1, 51):  # 遍历1到50的序号
    # 按patterns中定义的字段顺序，提取每个字段的值，组成列表
    item = [results[seq][key] for key in patterns]
    output.append(item)  # 加入到输出列表

# 打印提取结果，方便查看
print("提取结果（按序号1-50）：")
# 说明列表中每个元素的顺序对应的字段
print(
    "顺序：[累计输入token, 累计输出token, 累计总token, 总运行时间(秒), 内存峰值(MB), 内存平均值(MB), CPU峰值(%), CPU平均值(%)]")
# 逐个打印每个序号的结果（enumerate从1开始计数）
for i, data in enumerate(output, 1):
    print(f"序号{i}: {data}")

# ============== 以下是写入Excel的逻辑 ==============
from openpyxl import Workbook
# 创建Excel工作簿
wb = Workbook()
# 获取默认工作表
ws = wb.active
# 设置工作表名称
ws.title = "日志提取结果"

# 定义Excel列名（与提取的字段顺序对应）
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

# 写入列名（第一行）
ws.append(column_names)

# 写入数据（从第二行开始，按序号1-50顺序）
for row_data in output:
    ws.append(row_data)

# 保存Excel文件
excel_filename = "日志提取结果.xlsx"
wb.save(excel_filename)
print(f"结果已保存到 {excel_filename}")