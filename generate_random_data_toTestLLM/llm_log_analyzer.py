import re
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import ast
import matplotlib.font_manager


def get_available_fonts():
    """获取系统中可用的中文字体"""
    font_names = set()
    for font in matplotlib.font_manager.findSystemFonts():
        try:
            font_prop = matplotlib.font_manager.FontProperties(fname=font)
            font_names.add(font_prop.get_name())
        except:
            continue
    return font_names


def parse_log_file(file_path):
    """解析日志文件，提取所需数据"""
    data = defaultdict(list)
    token_pattern = re.compile(r'llm消耗的token情况: ({.*})')
    duration_pattern = re.compile(r'llm执行时长: (\d+\.\d+) 秒')

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # 提取token信息
            token_match = token_pattern.search(line)
            if token_match:
                try:
                    token_data = ast.literal_eval(token_match.group(1))
                    data['input_tokens'].append(token_data['input_tokens'])
                    data['output_tokens'].append(token_data['output_tokens'])
                    data['total_tokens'].append(token_data['total_tokens'])
                    data['reasoning'].append(token_data['output_token_details']['reasoning'])
                except Exception as e:
                    print(f"解析token数据时出错: {e}")
                    print(f"有问题的行: {line.strip()}")

            # 提取执行时长
            duration_match = duration_pattern.search(line)
            if duration_match:
                try:
                    data['duration'].append(float(duration_match.group(1)))
                except Exception as e:
                    print(f"解析执行时长时出错: {e}")
                    print(f"有问题的行: {line.strip()}")

    return data


def calculate_statistics(data):
    """计算各类数据的平均值、最小值和最大值"""
    stats = {}
    for key, values in data.items():
        if values:
            stats[key] = {
                'mean': np.mean(values),
                'min': np.min(values),
                'max': np.max(values)
            }
    return stats


def print_statistics(stats):
    """打印统计结果"""
    print("日志数据统计结果：")
    print("=" * 50)
    for metric, values in stats.items():
        print(f"{metric}:")
        print(f"  平均值: {values['mean']:.2f}")
        print(f"  最小值: {values['min']:.2f}")
        print(f"  最大值: {values['max']:.2f}")
        print("-" * 30)


def plot_data(data):
    """绘制折线图展示各指标的变化趋势"""
    # 获取系统可用字体
    available_fonts = get_available_fonts()
    print(f"\n系统可用字体: {sorted(available_fonts)[:5]}...")  # 打印部分可用字体

    # 字体优先级列表 - 只保留最通用的选项
    preferred_fonts = [
        "SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei",
        "Heiti TC", "Arial Unicode MS", "sans-serif"
    ]

    # 选择系统中实际存在的字体
    valid_fonts = [font for font in preferred_fonts if font in available_fonts]
    if not valid_fonts:
        print("警告: 未找到中文字体，可能导致中文显示异常")
        valid_fonts = ["sans-serif"]  # 最后的备选

    print(f"使用字体: {valid_fonts[0]}")
    plt.rcParams["font.family"] = valid_fonts
    plt.rcParams["axes.unicode_minus"] = False  # 正确显示负号

    # 创建2x2子图
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('LLM性能指标变化趋势', fontsize=16, fontweight='bold')

    # 指标配置（名称、图表标题、对应子图）
    metrics = [
        ('duration', '执行时长 (秒)', axes[0, 0]),
        ('input_tokens', '输入Token数量', axes[0, 1]),
        ('output_tokens', '输出Token数量', axes[1, 0]),
        ('total_tokens', '总Token数量', axes[1, 1])
    ]

    # 为每个指标绘制折线图
    for metric, title, ax in metrics:
        if data[metric]:
            ax.plot(
                range(1, len(data[metric]) + 1),
                data[metric],
                'o-',
                markersize=8,
                linewidth=2,
                label=f'共{len(data[metric])}次测试'
            )
            ax.set_title(title, fontsize=14, pad=10)
            ax.set_xlabel('测试次数', fontsize=12)
            ax.set_ylabel(title, fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.legend(fontsize=10)

    # 调整布局，避免标题重叠
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # 保存图片
    plt.savefig(
        'llm_metrics_trend.png',
        dpi=300,
        bbox_inches='tight',
        format='png',
        pil_kwargs={"optimize": True}
    )
    print("\n折线图已保存为 'llm_metrics_trend.png'")
    plt.show()


def main():
    log_file = 'deepseek_llm.log'
    try:
        print(f"正在解析日志文件: {log_file}")
        data = parse_log_file(log_file)

        if not data or all(len(v) == 0 for v in data.values()):
            print("未从日志文件中提取到有效数据")
            return

        stats = calculate_statistics(data)
        print_statistics(stats)
        plot_data(data)

        # 打印各指标原始列表
        print("\n各指标的测试记录列表：")
        print("=" * 50)
        for metric, values in data.items():
            print(f"{metric}: {values}")

    except FileNotFoundError:
        print(f"错误：找不到日志文件 '{log_file}'")
    except Exception as e:
        print(f"分析过程中发生错误：{str(e)}")


if __name__ == "__main__":
    main()

