import subprocess
import json
import os


def run_bandit_cmd(path: str, output_format: str = 'json', config_file: str = None) -> dict:
    """
    通过命令行调用Bandit进行安全扫描

    参数:
        path: 要扫描的文件或目录路径
        output_format: 输出格式，支持 'json'、'txt'、'csv'、'html' 等
        config_file: 自定义配置文件路径（可选）

    返回:
        dict: 包含执行结果的字典
    """
    # 构建Bandit命令
    # cmd = ['bandit', '-r', path, '-f', output_format]
    cmd = [r'D:\anaconda\envs\langchain_learning\Scripts\bandit.exe', '-r', path, '-f', output_format]

    if config_file:
        cmd.extend(['-c', config_file])

    try:
        # 执行命令并捕获输出
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,  # 若命令返回非零状态码，抛出CalledProcessError
            shell=True  # 关键修复：在Windows下需要这个参数才能正确找到bandit
        )

        # 解析JSON输出（如果格式为json）
        if output_format.lower() == 'json':
            return json.loads(result.stdout)
        else:
            return {
                'output': result.stdout,
                'returncode': result.returncode
            }

    except subprocess.CalledProcessError as e:
        # 命令执行失败
        return {
            'error': f"Bandit执行失败: {e.stderr}",
            'returncode': e.returncode,
            'stdout': e.stdout,
            'stderr': e.stderr,
            'command': ' '.join(cmd)
        }
    except json.JSONDecodeError as e:
        # JSON解析失败
        return {
            'error': f"解析Bandit输出失败: {str(e)}",
            'output': result.stdout,
            'command': ' '.join(cmd)
        }
    except Exception as e:
        # 其他异常
        return {
            'error': f"发生未知错误: {str(e)}",
            'command': ' '.join(cmd)
        }


# 使用示例
if __name__ == "__main__":
    check_result = run_bandit_cmd(r'agent_generate_code/my_code.py', output_format='json')
    print(check_result)
    # 注意：Windows路径中的反斜杠需要转义或使用原始字符串
    result = run_bandit_cmd(r'F:\PyCharm\langchain_test\temp_test.py', output_format='json')
    print(result)
    # # 处理结果
    # if 'error' in result:
    #     print(f"错误: {result['error']}")
    # else:
    #     if 'results' in result:
    #         print(f"发现 {len(result['results'])} 个安全问题")
    #         for issue in result['results']:
    #             print(f"- {issue['filename']}:{issue['line_number']}")
    #             print(f"  问题: {issue['issue_text']}")
    #             print(f"  严重度: {issue['issue_severity']}")
    #     else:
    #         print("扫描完成，未发现安全问题")