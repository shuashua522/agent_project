def func(x, y):
    """使用**运算符计算x的n次方"""
    return x ** n


def func2(x, n):
    """使用pow函数计算x的n次方"""
    return pow(x, n)


def eval(x):
    # 定义需要计算的n值列表（1,10,100,1000,10000）
    exponents = [10 ** i for i in range(5)]  # 生成[1,10,100,1000,10000]

    # 打开文件准备写入
    with open('result.md', 'w', encoding='utf-8') as f:
        # 写入Markdown表格头部
        f.write('| n值 | func1计算结果 | func2计算结果 |\n')
        f.write('|-----|--------------|--------------|\n')

        # 遍历每个n值，计算并写入结果
        for n in exponents:
            res1 = func1(x, n)
            res2 = func2(x, n)
            f.write(f'| {n} | {res1} | {res2} |\n')

# 示例用法：
eval(2)  # 计算2的各n次方并生成表格