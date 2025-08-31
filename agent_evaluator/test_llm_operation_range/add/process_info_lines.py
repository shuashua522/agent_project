import os


def process_txt_files():
    # 获取当前目录下所有文件
    current_dir = os.getcwd()
    files = os.listdir(current_dir)

    # 筛选出所有txt文件
    txt_files = [file for file in files if file.endswith('.txt')]

    if not txt_files:
        print("当前目录下没有找到txt文件")
        return

    for file in txt_files:
        file_path = os.path.join(current_dir, file)
        processed_lines = []

        # 读取GBK编码的文件内容并处理
        with open(file_path, 'r', encoding='gbk') as f:
            for line in f:
                # 检查行中是否包含"- INFO -"
                if '- INFO -' in line:
                    # 找到"- INFO -"的位置，截取后面的内容
                    index = line.find('- INFO -')
                    # 加上"- INFO -"的长度以完全移除该字符串
                    processed_line = line[index + len('- INFO -'):]
                    processed_lines.append(processed_line)
                else:
                    # 不包含目标字符串的行保持不变
                    processed_lines.append(line)

        # 以GBK编码写回处理后的内容
        with open(file_path, 'w', encoding='gbk') as f:
            f.writelines(processed_lines)

        print(f"已处理文件: {file}")

    print("所有txt文件处理完成")


if __name__ == "__main__":
    process_txt_files()
