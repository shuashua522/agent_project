def power_to_multiplication_str(n: int, m: int) -> str:
    """
    将n的m次方转换为m个n相乘的字符串

    参数:
        n: 底数（整数）
        m: 指数（非负整数）

    返回:
        str: m个n相乘的表达式字符串
    """
    # 处理指数为0的情况
    if m == 0:
        return "1"

    # 处理底数的符号（负数加括号）
    n_str = str(n)
    if n < 0:
        n_str = f"({n_str})"

    # 处理指数为1的情况
    if m == 1:
        return n_str

    # 常规情况：m个n用*连接
    return "*".join([n_str] * m)


def multiply_to_addition_str(n: int, m: int) -> str:
    """
    将n×m转换为m个n相加的字符串

    参数:
        n: 被乘数（整数）
        m: 乘数（非负整数）

    返回:
        str: m个n相加的表达式字符串
    """
    # 处理乘数为0的情况：0个n相加结果为0
    if m == 0:
        return "0"

    # 处理被乘数的符号（负数加括号）
    n_str = str(n)
    if n < 0:
        n_str = f"({n_str})"

    # 处理乘数为1的情况：仅1个n
    if m == 1:
        return n_str

    # 常规情况：m个n用+连接
    return "+".join([n_str] * m)

def count_integer_digits(num: int) -> int:
    # 处理零的特殊情况
    if num == 0:
        return 1
    # 去掉负号，转为字符串后取长度
    return len(str(abs(num)))


