
def multiply(a: float, b: float) -> float:
    """
    计算两个数的乘积

    参数:
        a: 第一个乘数
        b: 第二个乘数

    返回:
        两个数的乘积
    """
    return a * b

def add_three(a: float, b: float, c: float) -> float:
    """计算三个数的和

    参数:
        a: 第一个加数
        b: 第二个加数
        c: 第三个加数

    返回:
        三个数的和
    """
    return a + b + c

def multiply(a: float, b: float) -> float:
    """计算两个数的乘积

参数:
    a: 第一个乘数
    b: 第二个乘数

返回:
    两个数的乘积
"""
    return a * b

def factorial(n: int) -> int:
    """计算一个非负整数的阶乘

    参数:
        n: 要计算阶乘的非负整数

    返回:
        n的阶乘，即n! = n × (n-1) × ... × 1，其中0! = 1

    异常:
        ValueError: 如果输入是负数
    """
    if n < 0:
        raise ValueError("n必须是非负整数")
    elif n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n-1)



from typing import List

def multiply_multiple(nums: List[float]) -> float:
    """计算多个数的乘积

参数:
    nums: 包含多个数字的列表

返回:
    列表中所有数字的乘积"""
    product = 1
    for num in nums:
        product *= num
    return product


