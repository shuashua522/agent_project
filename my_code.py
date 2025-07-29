import math

# 定义计算对称中心最小值的函数
def find_a_min():
    a = 0.1  # 从一个小值开始
    while True:
        f_a = 2 * math.tan(a - math.pi / 3)
        f_neg_a = -2 * math.tan(a - math.pi / 3)
        if math.isclose(f_a, f_neg_a, rel_tol=1e-9):
            return a
        a += 0.01  # 逐渐增加a的值

# 计算最小的a
if __name__ == "__main__":
    a_min_value = find_a_min()
    print(a_min_value)