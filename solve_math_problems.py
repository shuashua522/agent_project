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

def get_last_answered_question(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # 使用正则表达式匹配所有答案行
            pattern = r'^\d+\.\s+(.*)$'
            answers = re.findall(pattern, content, re.MULTILINE)
            return len(answers) if answers else 0
    except FileNotFoundError:
        return 0  # 文件不存在时返回0
    except Exception as e:
        print(f"错误：读取文件时发生异常：{e}")
        return 0


def append_answer(file_path, problem_index, answer):
    try:
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(f"{problem_index}. {answer}\n")
    except Exception as e:
        print(f"错误：写入答案时发生异常：{e}")


from project_03 import func

if __name__ == "__main__":
    # 问题列表
    file_path = "test.md"
    problems = extract_math_problems(file_path)

    answer_file = "answer.md"

    # 获取已解答的最后一题序号
    last_answered = get_last_answered_question(answer_file)
    print(f"已解答到第 {last_answered} 题")

    # 从下一题开始解答剩余问题
    for i in range(last_answered, len(problems)):
        problem_index = i + 1
        problem = problems[i]
        print(f"正在解答第 {problem_index} 题：{problem}")

        # 调用func函数解答问题
        answer = func(problem)

        # 将答案追加到answer.md
        append_answer(answer_file, problem_index, answer)
        print(f"已解答第 {problem_index} 题，答案已保存")