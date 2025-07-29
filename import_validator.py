import ast
import subprocess
import sys
from pathlib import Path


def extract_imports(source_file: str, target_file: str) -> None:
    """使用AST从源文件中提取所有import语句并写入目标文件"""
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：找不到源文件 {source_file}")
        return

    # 解析源代码为AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"错误：源文件语法错误 - {e}")
        return

    # 收集所有导入节点
    import_nodes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            import_nodes.append(node)

    # 生成导入语句
    import_statements = []
    for node in import_nodes:
        if isinstance(node, ast.Import):
            # 处理 import a, b as c 形式
            names = []
            for alias in node.names:
                if alias.asname:
                    names.append(f"{alias.name} as {alias.asname}")
                else:
                    names.append(alias.name)
            import_statements.append(f"import {', '.join(names)}")
        elif isinstance(node, ast.ImportFrom):
            # 处理 from a import b, c as d 形式
            module = node.module or ''
            level = node.level * '.'
            names = []
            for alias in node.names:
                if alias.asname:
                    names.append(f"{alias.name} as {alias.asname}")
                else:
                    names.append(alias.name)
            if node.module is None and node.level == 0:
                # 处理隐式相对导入（虽然在Python 3中已弃用）
                import_statements.append(f"from . import {', '.join(names)}")
            else:
                import_statements.append(f"from {level}{module} import {', '.join(names)}")

    # 写入目标文件
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(import_statements))


def run_import_check(import_file: str) -> tuple[bool, str]:
    """运行导入检查文件并返回结果"""
    result = subprocess.run(
        [sys.executable, import_file],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return True, "所有模块导入成功"
    else:
        return False, result.stderr


def main():
    source_file = "my_code.py"
    target_file = "import_try.py"

    # 提取导入语句
    extract_imports(source_file, target_file)
    print(f"已提取导入语句到 {target_file}")

    # 运行导入检查
    success, message = run_import_check(target_file)

    if success:
        print("导入检查结果：True")
    else:
        print("导入检查结果：False")
        print("异常信息：")
        print(message)


if __name__ == "__main__":
    main()