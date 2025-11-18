#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接从 Python 代码生成 HTML 文档

使用 pdoc 或 pydoc 自动生成 HTML 文档，无需配置，一键生成。

支持的工具：
1. pdoc3 - 推荐，功能强大，样式美观
2. pdoc - 轻量级，简单易用
3. pydoc - Python 内置，但样式基础
"""

import os
import subprocess
import sys
from pathlib import Path

# 设置输出编码为 UTF-8（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def check_package_installed(package_name: str) -> bool:
    """检查包是否已安装"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def install_pdoc3():
    """安装 pdoc3"""
    print("正在安装 pdoc3...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdoc3"])
    print("[OK] pdoc3 安装完成")


def generate_with_pdoc3(module_path: str, output_dir: Path, python_path: str = None):
    """使用 pdoc3 生成 HTML 文档"""
    try:
        import pdoc
    except ImportError:
        print("pdoc3 未安装，正在安装...")
        install_pdoc3()
        import pdoc
    
    print(f"使用 pdoc3 生成文档...")
    print(f"模块路径: {module_path}")
    print(f"输出目录: {output_dir}")
    if python_path:
        print(f"Python 路径: {python_path}")
    print()
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用 pdoc 生成 HTML
    # pdoc3 的命令行用法：pdoc --html --output-dir <输出目录> <模块路径>
    # 添加 --skip-errors 选项，跳过导入错误（如缺少依赖）
    cmd = [sys.executable, "-m", "pdoc", "--html", "--output-dir", str(output_dir), "--skip-errors", module_path]
    
    # 设置环境变量，确保 Python 能找到模块
    env = os.environ.copy()
    if python_path:
        # 将 code_liu 路径添加到 PYTHONPATH
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{python_path}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = python_path
    
    print(f"执行命令: {' '.join(cmd)}")
    if python_path:
        print(f"PYTHONPATH: {env.get('PYTHONPATH', '')}")
    print()
    
    try:
        subprocess.check_call(cmd, env=env)
        
        # 查找生成的 HTML 文件
        html_path = output_dir / module_path.replace('.', '/') / 'index.html'
        if not html_path.exists():
            # 尝试其他可能的路径
            html_path = output_dir / f"{module_path.replace('.', '_')}.html"
        
        if html_path.exists():
            print(f"\n[OK] HTML 文档已生成")
            print(f"打开文件: {html_path}")
        else:
            print(f"\n[OK] HTML 文档已生成到目录: {output_dir}")
            print(f"请查看目录中的 HTML 文件")
        
    except subprocess.CalledProcessError as e:
        print(f"\n错误: 生成文档失败")
        print(f"提示: 确保模块路径正确，并且代码可以正常导入")
        print(f"尝试: python -m pdoc --help 查看帮助")
        print(f"\n调试信息:")
        print(f"  - 模块路径: {module_path}")
        print(f"  - Python 路径: {sys.path[:3]}")
        if python_path:
            print(f"  - PYTHONPATH: {python_path}")


def generate_with_pydoc(module_path: str, output_file: Path):
    """使用 Python 内置的 pydoc 生成 HTML（样式较基础）"""
    print(f"使用 pydoc 生成文档...")
    
    # 确保输出目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # pydoc 生成 HTML
    cmd = [
        sys.executable, "-m", "pydoc",
        "-w", module_path
    ]
    
    subprocess.check_call(cmd, cwd=str(output_file.parent))
    
    # pydoc 会在当前目录生成 HTML 文件
    html_file = output_file.parent / f"{module_path.replace('.', '_')}.html"
    if html_file.exists():
        print(f"\n[OK] HTML 文档已生成: {html_file}")
        print(f"打开 {html_file} 查看")
    else:
        print(f"警告: 未找到生成的 HTML 文件")


# ============================================================================
# 配置区域 - 在这里修改输入输出路径（支持绝对路径和相对路径）
# ============================================================================

# 输入配置：要生成文档的源代码路径
# 支持绝对路径或相对路径（相对项目根目录）
INPUT_PATH = r"D:\Python_project\Markdown\code_liu\RCSB_PDB"  # 直接使用绝对路径，最简单！

# 或者使用相对路径（取消注释使用）
# INPUT_PATH = "code_liu/RCSB_PDB"  # 相对项目根目录

# 或者使用模块路径（取消注释使用）
# INPUT_MODULE_PATH = "RCSB_PDB.src.spider.rcsb_pdb.rcsb_pdb_spider"  # 模块路径

# 输出配置：生成的 HTML 文档保存位置
OUTPUT_DIR = r"D:\Python_project\Markdown\pdoc3_doc\docs\RCSB"  # 使用绝对路径，最简单！

# 或者使用相对路径（取消注释使用）
# OUTPUT_DIR = "docs/RCSB"  # 相对脚本所在目录

# 工具配置
USE_PDOC3 = True  # True 使用 pdoc3（推荐），False 使用 pydoc（Python 内置）

# ============================================================================
# 以下代码无需修改
# ============================================================================


def path_to_module_path(input_path: Path, code_liu_root: Path) -> str:
    """将文件/目录路径转换为模块路径"""
    try:
        rel_path = input_path.relative_to(code_liu_root)
        if input_path.is_file():
            # 文件路径：去掉 .py 扩展名
            module_path = str(rel_path.with_suffix("")).replace("/", ".").replace("\\", ".")
        else:
            # 目录路径
            module_path = str(rel_path).replace("/", ".").replace("\\", ".")
        return module_path if module_path else None
    except ValueError as e:
        # 路径不在 code_liu_root 下
        return None


def find_code_liu_root(input_path: Path) -> Path:
    """从输入路径向上查找 code_liu 目录"""
    current = input_path if input_path.is_dir() else input_path.parent
    while current != current.parent:  # 直到根目录
        if current.name == "code_liu" and current.is_dir():
            return current
        current = current.parent
    return None


def main():
    """主函数"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    code_liu_root = project_root / "code_liu"
    
    # 解析输入配置（优先级：INPUT_PATH > INPUT_MODULE_PATH）
    input_module_path = None
    input_path_obj = None
    actual_code_liu_root = None
    
    # 方式1: 使用 INPUT_PATH（文件或目录路径，支持绝对路径）
    try:
        input_path_str = INPUT_PATH
        if input_path_str:
            # 判断是绝对路径还是相对路径
            if Path(input_path_str).is_absolute():
                input_path_obj = Path(input_path_str)
            else:
                input_path_obj = project_root / input_path_str
            
            if input_path_obj.exists():
                if input_path_obj.is_file():
                    print(f"✓ 输入: 文件路径 - {input_path_obj}")
                else:
                    print(f"✓ 输入: 目录路径 - {input_path_obj}")
                
                # 查找 code_liu 目录（优先从输入路径查找，然后使用默认位置）
                actual_code_liu_root = find_code_liu_root(input_path_obj)
                if not actual_code_liu_root:
                    actual_code_liu_root = code_liu_root if code_liu_root.exists() else None
                
                if actual_code_liu_root:
                    print(f"✓ 找到 code_liu 目录: {actual_code_liu_root}")
                    input_module_path = path_to_module_path(input_path_obj, actual_code_liu_root)
                    if input_module_path:
                        print(f"✓ 模块路径: {input_module_path}")
                    else:
                        # 如果不在 code_liu 下，尝试从路径中提取
                        path_str = str(input_path_obj)
                        if "code_liu" in path_str:
                            parts = path_str.split("code_liu")
                            if len(parts) > 1:
                                rel_part = parts[1].lstrip("\\/")
                                input_module_path = rel_part.replace("\\", ".").replace("/", ".")
                                if input_path_obj.is_file():
                                    input_module_path = input_module_path.replace(".py", "")
                                print(f"提示: 从路径提取模块名: {input_module_path}")
                            else:
                                input_module_path = input_path_obj.stem if input_path_obj.is_file() else input_path_obj.name
                                print(f"提示: 使用路径名: {input_module_path}")
                        else:
                            input_module_path = input_path_obj.stem if input_path_obj.is_file() else input_path_obj.name
                            print(f"提示: 路径不包含 code_liu，使用路径名: {input_module_path}")
                else:
                    # code_liu 目录不存在，直接使用路径名
                    input_module_path = input_path_obj.stem if input_path_obj.is_file() else input_path_obj.name
                    print(f"警告: 未找到 code_liu 目录，使用路径名: {input_module_path}")
                    # 尝试使用输入路径的父目录作为 code_liu
                    if input_path_obj.is_dir():
                        actual_code_liu_root = input_path_obj.parent
                    else:
                        actual_code_liu_root = input_path_obj.parent.parent
                
                # 确保 input_module_path 已设置
                if not input_module_path or input_module_path.strip() == "":
                    input_module_path = input_path_obj.stem if input_path_obj.is_file() else input_path_obj.name
                    print(f"警告: 使用默认路径名: {input_module_path}")
            else:
                print(f"错误: 路径不存在 {input_path_obj}")
                return
    except NameError:
        # INPUT_PATH 未定义，检查模块路径
        pass
    
    # 方式2: 使用 INPUT_MODULE_PATH（模块路径）
    if not input_module_path:
        try:
            input_module_path = INPUT_MODULE_PATH
            if input_module_path:
                print(f"✓ 输入: 模块路径 - {input_module_path}")
                # 如果使用模块路径，尝试找到 code_liu
                if not actual_code_liu_root:
                    actual_code_liu_root = code_liu_root if code_liu_root.exists() else None
            else:
                print("错误: INPUT_MODULE_PATH 为空")
                return
        except NameError:
            print("错误: 未配置输入路径")
            print("请在脚本顶部配置：")
            print("  - INPUT_PATH: 文件或目录路径（支持绝对路径，例如: r'D:\\path\\to\\code'）")
            print("  - INPUT_MODULE_PATH: 模块路径（例如: 'NTRT.data_cleaner'）")
            return
    
    # 解析输出配置
    try:
        output_dir_str = OUTPUT_DIR
    except NameError:
        output_dir_str = "docs/html_docs"
    
    # 判断是绝对路径还是相对路径
    if Path(output_dir_str).is_absolute():
        output_dir = Path(output_dir_str)
    else:
        output_dir = script_dir / output_dir_str
    
    # 添加 code_liu 目录到 Python 路径（必须在导入模块之前）
    if actual_code_liu_root and actual_code_liu_root.exists():
        code_liu_path_str = str(actual_code_liu_root)
        if code_liu_path_str not in sys.path:
            sys.path.insert(0, code_liu_path_str)
            print(f"✓ 已添加 Python 路径: {code_liu_path_str}")
    elif code_liu_root.exists():
        code_liu_path_str = str(code_liu_root)
        if code_liu_path_str not in sys.path:
            sys.path.insert(0, code_liu_path_str)
            print(f"✓ 已添加 Python 路径: {code_liu_path_str}")
    
    print("=" * 60)
    print("直接从代码生成 HTML 文档")
    print("=" * 60)
    print()
    print(f"输入: {input_module_path}")
    print(f"输出: {output_dir}")
    print()
    
    # 获取工具配置
    try:
        use_pdoc3 = USE_PDOC3
    except NameError:
        use_pdoc3 = True
    
    # 获取 Python 路径（用于传递给 pdoc）
    python_path = None
    if actual_code_liu_root and actual_code_liu_root.exists():
        python_path = str(actual_code_liu_root)
    elif code_liu_root.exists():
        python_path = str(code_liu_root)
    
    if use_pdoc3:
        generate_with_pdoc3(input_module_path, output_dir, python_path)
    else:
        output_file = output_dir / f"{input_module_path.replace('.', '_')}.html"
        generate_with_pydoc(input_module_path, output_file)
    
    print()
    print("=" * 60)
    print("完成！")
    print("=" * 60)
    print()
    print("=" * 60)
    print("配置说明")
    print("=" * 60)
    print("修改脚本顶部的配置可以改变输入输出：")
    print("- INPUT_MODULE_PATH: 模块路径（例如: 'NTRT.data_cleaner'）")
    print("- INPUT_FILE_PATH: 文件路径（例如: 'code_liu/NTRT/data_cleaner.py'）")
    print("- INPUT_DIR_PATH: 目录路径（例如: 'code_liu/NTRT'）")
    print("- OUTPUT_DIR: 输出目录（例如: 'docs/html_docs'）")
    print("- USE_PDOC3: 使用的工具（True=pdoc3, False=pydoc）")
    print()
    print("优势：")
    print("- ✅ 完全自动化，无需写 Markdown")
    print("- ✅ 零配置，一条命令生成")
    print("- ✅ 代码更新，重新运行即可")
    print("- ✅ 比 MkDocs 简单很多！")


if __name__ == "__main__":
    main()

