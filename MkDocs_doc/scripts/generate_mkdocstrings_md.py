#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成包含 mkdocstrings 语法的 .md 文件

这个脚本会：
1. 扫描 Python 代码目录
2. 自动发现所有类和函数
3. 生成包含 mkdocstrings 语法的 .md 文件
4. 你只需要运行一次，之后代码更新时再运行即可
"""

import ast
import os
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict


def find_python_files(src_path: Path) -> List[Path]:
    """查找所有 Python 文件"""
    python_files = []
    for py_file in src_path.rglob("*.py"):
        # 排除不需要的目录
        if "__pycache__" in str(py_file):
            continue
        if ".venv" in str(py_file):
            continue
        if "site-packages" in str(py_file):
            continue
        if py_file.name == "__init__.py":
            continue
        python_files.append(py_file)
    return sorted(python_files)


def extract_classes_and_functions(file_path: Path, base_path: Path) -> Tuple[List[str], List[str]]:
    """提取文件中的类和函数"""
    classes = []
    functions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 计算模块路径（从 base_path 开始，去掉 code_liu 前缀）
        try:
            rel_path = file_path.relative_to(base_path)
        except ValueError:
            # 如果不在 base_path 下，尝试从 base_path.parent 开始
            rel_path = file_path.relative_to(base_path.parent)
        module_path = str(rel_path.with_suffix("")).replace(os.sep, ".")
        
        # 如果路径以 code_liu. 开头，去掉它
        if module_path.startswith("code_liu."):
            module_path = module_path[len("code_liu."):]
        
        # 解析 AST
        tree = ast.parse(content, filename=str(file_path))
        
        # 使用访问者模式提取类和函数
        class Visitor(ast.NodeVisitor):
            def __init__(self):
                self.classes = []
                self.functions = []
                self.in_class = False
            
            def visit_ClassDef(self, node):
                # 跳过私有类
                if not node.name.startswith("_"):
                    self.classes.append(f"{module_path}.{node.name}")
                # 标记进入类
                old_in_class = self.in_class
                self.in_class = True
                self.generic_visit(node)
                self.in_class = old_in_class
            
            def visit_FunctionDef(self, node):
                # 只提取模块级别的函数（不在类中）
                if not self.in_class and not node.name.startswith("_"):
                    self.functions.append(f"{module_path}.{node.name}")
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                # 只提取模块级别的异步函数（不在类中）
                if not self.in_class and not node.name.startswith("_"):
                    self.functions.append(f"{module_path}.{node.name}")
                self.generic_visit(node)
        
        visitor = Visitor()
        visitor.visit(tree)
        classes = visitor.classes
        functions = visitor.functions
        
    except Exception as e:
        print(f"警告: 无法解析 {file_path}: {e}")
    
    return classes, functions


def categorize_by_project(src_path: Path, base_path: Path) -> Dict[str, List[Tuple[str, str]]]:
    """按项目分类"""
    categories = defaultdict(list)
    
    python_files = find_python_files(src_path)
    
    for py_file in python_files:
        classes, functions = extract_classes_and_functions(py_file, base_path)
        
        # 根据路径分类
        rel_path = py_file.relative_to(src_path)
        path_parts = rel_path.parts
        
        if len(path_parts) == 1:
            # 直接在根目录
            if "data_cleaner" in py_file.name:
                categories["数据清洗模块"].extend([(c, "class") for c in classes])
            elif "base_mysql" in py_file.name:
                categories["数据库模块"].extend([(c, "class") for c in classes])
            else:
                categories["其他模块"].extend([(c, "class") for c in classes])
        elif path_parts[0] == "application":
            categories["应用模块"].extend([(c, "class") for c in classes])
        elif path_parts[0] == "src":
            if "spider" in str(py_file):
                categories["爬虫模块"].extend([(c, "class") for c in classes])
            elif "pipeline" in str(py_file):
                categories["管道模块"].extend([(c, "class") for c in classes])
            elif "item" in str(py_file):
                categories["数据项模块"].extend([(c, "class") for c in classes])
            else:
                categories["其他模块"].extend([(c, "class") for c in classes])
        else:
            categories["其他模块"].extend([(c, "class") for c in classes])
    
    return dict(categories)


def generate_mkdocstrings_markdown(categories: Dict[str, List[Tuple[str, str]]], 
                                    project_name: str = "项目") -> str:
    """生成包含 mkdocstrings 语法的 Markdown"""
    lines = [f"# {project_name} - API 参考", ""]
    
    # 按类别输出
    for category, items in categories.items():
        if not items:
            continue
        
        lines.append(f"## {category}")
        lines.append("")
        
        for item_path, item_type in items:
            # 提取类名或函数名
            name = item_path.split(".")[-1]
            
            lines.append(f"### {name}")
            lines.append("")
            
            # 生成 mkdocstrings 语法
            lines.append(f"::: {item_path}")
            lines.append("    handler: python")
            lines.append("    options:")
            lines.append("      show_root_heading: true")
            lines.append("      show_source: true")
            lines.append("      show_signature_annotations: true")
            lines.append("")
    
    return "\n".join(lines)


def auto_generate_for_project(project_name: str, src_path: Path, 
                               output_file: Path, base_path: Path):
    """为项目自动生成 API 文档"""
    print(f"扫描项目: {project_name}")
    print(f"源码路径: {src_path}")
    
    if not src_path.exists():
        print(f"错误: 路径不存在 {src_path}")
        return
    
    # 分类
    categories = categorize_by_project(src_path, base_path)
    
    # 打印统计
    print(f"\n发现的类和函数:")
    for category, items in categories.items():
        print(f"  {category}: {len(items)} 个")
        for item_path, item_type in items[:5]:  # 只显示前5个
            print(f"    - {item_path}")
        if len(items) > 5:
            print(f"    ... 还有 {len(items) - 5} 个")
    
    # 生成 Markdown
    markdown_content = generate_mkdocstrings_markdown(categories, project_name)
    
    # 保存
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"\n[OK] 已生成 API 文档: {output_file}")
    print(f"   共生成 {sum(len(c) for c in categories.values())} 个类/函数的文档")


def main():
    """主函数"""
    script_dir = Path(__file__).parent
    mkdocs_doc_dir = script_dir.parent
    project_root = mkdocs_doc_dir.parent
    
    # RCSB_PDB 项目（输出到 ntrt 目录）
    rcsb_src = project_root / "code_liu" / "RCSB_PDB" / "src"
    rcsb_output = mkdocs_doc_dir / "docs" / "projects" / "ntrt" / "api.md"
    
    if rcsb_src.exists():
        auto_generate_for_project(
            "RCSB PDB 项目",
            rcsb_src,
            rcsb_output,
            project_root / "code_liu"
        )
    else:
        print(f"警告: RCSB PDB 源码目录不存在 {rcsb_src}")
    
    print("\n" + "="*50)
    print("[OK] 自动生成完成！")
    print("\n现在你可以：")
    print("1. 运行 mkdocs serve 查看文档")
    print("2. 编辑生成的 api.md 文件，添加描述和说明")
    print("3. 代码更新后，重新运行此脚本更新文档")


if __name__ == "__main__":
    main()

