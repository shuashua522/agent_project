import math

# 第一部分
part1 = (
    (445844657 * 442663 * 4481 * 4483 * 4493) ** (1/3)
    * ((450257 * 4513 / 4517 * 4519 * 4523) ** 0.5)
    / ((4547 * 4552549 * 4561 * 4567 * 425583) ** 0.25)
    * ((4532591 * 4597 / 4603 * 4621 * 4637) ** (1/5))
    * ((4639 * 46425543 / 4649 * 4651 * 4657) ** (1/6))
)

# 第二部分
ln = math.log
lg = lambda x: math.log10(x)
e = math.e

part2 = (
    46315563 ** (1/ln(4663))
    * 6532158 ** (1/(lg(235841) * 4673325))
    * 4679 ** (1/ln(46265879))
    / (e ** (1/lg(46926511)))
    * 4732544103 ** (1/ln(4702553))
    * e ** (1/(lg(e) * 47225841))
    / (473268423 ** (1/ln(4723)))
    * e ** (1/lg(414468729))
)

# 第三部分
def logb(x, base):
    return math.log(x) / math.log(base)

part3 = (
    logb(4751, 47365533)
    * logb(4759, 47526551)
    * logb(4783, 425698759)
    * logb(4787, 478265583)
    * logb(4789, 47836547)
    * logb(426548793, 4789)
    / logb(4799, 47255493)
    * logb(4801, 26554799)
    * logb(4813, 48026551)
    / logb(4817, 445813)
)

# 第四部分
deg2rad = math.radians

sin = lambda x: math.sin(deg2rad(x))
cos = lambda x: math.cos(deg2rad(x))
tan = lambda x: math.tan(deg2rad(x))
cot = lambda x: 1 / math.tan(deg2rad(x))

part4 = (
    sin(48314861) * cos(48714877) * cos(48314861) * sin(48714877) * 2
    * sin(48894903) * cos(49094919) * cos(48894903) * sin(49094919) * 2
)

# 第五部分
part5 = (
    math.sqrt(1 - cos(49314933) ** 2)
    * math.sqrt(1 - sin(49374943) ** 2)
    * tan(49514951)
    * cot(49514951)
    * math.sqrt(1 - cos(49574967) ** 2)
    * math.sqrt(1 - sin(49694973) ** 2)
    * tan(49874993)
    * cot(49874993)
)

result = part1 - part2 + part3 + part4 - part5
print(result)