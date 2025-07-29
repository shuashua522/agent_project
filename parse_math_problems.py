import re


def extract_math_problems(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # 使用正则表达式匹配有序列表项
            pattern = r'^\d+\.\s+(.*)$'
            problems = re.findall(pattern, content, re.MULTILINE)
            return problems
    except FileNotFoundError:
        print(f"错误：找不到文件 '{file_path}'")
        return []
    except Exception as e:
        print(f"错误：读取文件时发生异常：{e}")
        return []


if __name__ == "__main__":
    file_path = "test.md"
    problems = extract_math_problems(file_path)

    if problems:
        print(f"成功从 {file_path} 中提取 {len(problems)} 道数学题")
        for i, problem in enumerate(problems, 1):
            print(f"{i}. {problem}")
    else:
        print("未找到数学题，请检查文件格式是否为有序列表")