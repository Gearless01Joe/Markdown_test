#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 Python 代码转换为 Markdown 文档

功能：
- 解析 Python 文件，提取类、函数、docstring
- 生成结构化的 Markdown 文档
- 支持批量处理目录
"""

import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    docstring: str
    args: List[Tuple[str, Optional[str]]]  # (name, annotation)
    returns: Optional[str]
    is_async: bool
    is_static: bool
    is_classmethod: bool
    line_no: int


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    docstring: str
    bases: List[str]
    methods: List[FunctionInfo]
    attributes: List[Tuple[str, Optional[str]]]  # (name, annotation)
    line_no: int


@dataclass
class ModuleInfo:
    """模块信息"""
    docstring: str
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    imports: List[str]


class CodeParser:
    """代码解析器"""
    
    def __init__(self):
        self.module_info = None
    
    def parse_file(self, file_path: Path) -> ModuleInfo:
        """解析 Python 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            print(f"警告: 无法解析 {file_path}: {e}")
            return ModuleInfo("", [], [], [])
        
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        return visitor.get_module_info()
    
    def parse_docstring_params(self, docstring: str) -> Dict[str, str]:
        """从 docstring 中解析参数说明（优先支持 Sphinx 风格）"""
        params = {}
        if not docstring:
            return params
        
        # Sphinx 风格: :param name: description 或 :param name (type): description
        # 优先解析 Sphinx 风格
        sphinx_pattern = r':param\s+(\w+)(?:\s*\([^)]+\))?\s*:\s*([^\n]+)'
        for match in re.finditer(sphinx_pattern, docstring):
            param_name = match.group(1)
            param_desc = match.group(2).strip()
            # 如果参数已存在，合并描述（可能有多行）
            if param_name in params:
                params[param_name] += " " + param_desc
            else:
                params[param_name] = param_desc
        
        # 如果 Sphinx 风格没有找到，尝试 Google 风格
        if not params:
            # Google 风格: Args: 或 Parameters:
            args_pattern = r'(?:Args?|Parameters?):\s*\n((?:\s+[^\n:]+\s*:\s*[^\n]+\n?)+)'
            match = re.search(args_pattern, docstring, re.MULTILINE)
            if match:
                args_text = match.group(1)
                for line in args_text.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        param_name, param_desc = line.split(':', 1)
                        params[param_name.strip()] = param_desc.strip()
        
        return params
    
    def parse_docstring_returns(self, docstring: str) -> Optional[str]:
        """从 docstring 中解析返回值说明（优先支持 Sphinx 风格）"""
        if not docstring:
            return None
        
        # Sphinx 风格: :return: description 或 :rtype: type
        # 优先解析 Sphinx 风格
        sphinx_return_pattern = r':return:\s*([^\n]+)'
        match = re.search(sphinx_return_pattern, docstring)
        if match:
            return_desc = match.group(1).strip()
            # 尝试获取类型信息
            rtype_pattern = r':rtype:\s*([^\n]+)'
            rtype_match = re.search(rtype_pattern, docstring)
            if rtype_match:
                return_type = rtype_match.group(1).strip()
                return f"{return_type}: {return_desc}"
            return return_desc
        
        # 如果 Sphinx 风格没有找到，尝试 Google 风格
        # Google 风格: Returns: 或 Return:
        returns_pattern = r'(?:Returns?):\s*\n\s*([^\n]+)'
        match = re.search(returns_pattern, docstring, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        return None
    
    def parse_docstring_raises(self, docstring: str) -> Dict[str, str]:
        """从 docstring 中解析异常说明（Sphinx 风格）"""
        raises = {}
        if not docstring:
            return raises
        
        # Sphinx 风格: :raises ExceptionType: description 或 :raise ExceptionType: description
        sphinx_raises_pattern = r':(?:raises?|except)\s+(\w+(?:\.\w+)*)\s*:\s*([^\n]+)'
        for match in re.finditer(sphinx_raises_pattern, docstring):
            exc_type = match.group(1)
            exc_desc = match.group(2).strip()
            raises[exc_type] = exc_desc
        
        return raises


class CodeVisitor(ast.NodeVisitor):
    """AST 访问器"""
    
    def __init__(self):
        self.module_docstring = ""
        self.classes: List[ClassInfo] = []
        self.functions: List[FunctionInfo] = []
        self.imports: List[str] = []
        self.current_class = None
    
    def visit_Module(self, node):
        """访问模块"""
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            self.module_docstring = node.body[0].value.s
        elif node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            self.module_docstring = node.body[0].value.value
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """访问 import 语句"""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """访问 from ... import 语句"""
        module = node.module or ""
        for alias in node.names:
            self.imports.append(f"{module}.{alias.name}")
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """访问类定义"""
        docstring = ast.get_docstring(node) or ""
        bases = [self._get_name(base) for base in node.bases]
        
        methods = []
        attributes = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                func_info = self._extract_function_info(item)
                methods.append(func_info)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_type = None
                        if item.value:
                            attr_type = self._get_type_hint(item.value)
                        attributes.append((target.id, attr_type))
        
        class_info = ClassInfo(
            name=node.name,
            docstring=docstring,
            bases=bases,
            methods=methods,
            attributes=attributes,
            line_no=node.lineno
        )
        
        self.classes.append(class_info)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """访问函数定义（模块级别）"""
        if self.current_class is None:  # 只处理模块级别的函数
            func_info = self._extract_function_info(node)
            self.functions.append(func_info)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        """访问异步函数定义（模块级别）"""
        if self.current_class is None:
            func_info = self._extract_function_info(node)
            self.functions.append(func_info)
        self.generic_visit(node)
    
    def _extract_function_info(self, node) -> FunctionInfo:
        """提取函数信息"""
        docstring = ast.get_docstring(node) or ""
        args = []
        
        for arg in node.args.args:
            arg_name = arg.arg
            arg_type = None
            if arg.annotation:
                arg_type = self._get_name(arg.annotation)
            args.append((arg_name, arg_type))
        
        returns = None
        if node.returns:
            returns = self._get_name(node.returns)
        
        is_async = isinstance(node, ast.AsyncFunctionDef)
        is_static = any(isinstance(d, ast.Name) and d.id == 'staticmethod' 
                       for d in node.decorator_list)
        is_classmethod = any(isinstance(d, ast.Name) and d.id == 'classmethod' 
                            for d in node.decorator_list)
        
        return FunctionInfo(
            name=node.name,
            docstring=docstring,
            args=args,
            returns=returns,
            is_async=is_async,
            is_static=is_static,
            is_classmethod=is_classmethod,
            line_no=node.lineno
        )
    
    def _get_name(self, node) -> str:
        """获取节点名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return str(node)
    
    def _get_type_hint(self, node) -> Optional[str]:
        """获取类型提示"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return type(node.value).__name__
        return None
    
    def get_module_info(self) -> ModuleInfo:
        """获取模块信息"""
        return ModuleInfo(
            docstring=self.module_docstring,
            classes=self.classes,
            functions=self.functions,
            imports=self.imports
        )


class MarkdownGenerator:
    """Markdown 生成器"""
    
    def __init__(self, parser: CodeParser):
        self.parser = parser
    
    def generate(self, module_info: ModuleInfo, file_path: Path, 
                 base_path: Path) -> str:
        """生成 Markdown 内容"""
        lines = []
        
        # 计算模块路径
        rel_path = file_path.relative_to(base_path.parent)
        module_path = str(rel_path.with_suffix("")).replace(os.sep, ".")
        module_name = file_path.stem
        
        # 标题
        lines.append(f"# {module_name}")
        lines.append("")
        
        # 模块 docstring
        if module_info.docstring:
            # 清理 docstring（移除 # @Time 等注释格式）
            clean_doc = self._clean_docstring(module_info.docstring)
            lines.append(clean_doc)
            lines.append("")
        
        # 模块路径
        lines.append(f"**模块路径**: `{module_path}`")
        lines.append("")
        
        # 导入信息
        if module_info.imports:
            lines.append("## 导入")
            lines.append("")
            for imp in sorted(set(module_info.imports))[:10]:  # 只显示前10个
                lines.append(f"- `{imp}`")
            lines.append("")
        
        # 类文档
        if module_info.classes:
            lines.append("## 类")
            lines.append("")
            
            for class_info in module_info.classes:
                lines.append(f"### {class_info.name}")
                lines.append("")
                
                # 类 docstring
                if class_info.docstring:
                    clean_doc = self._clean_docstring(class_info.docstring)
                    lines.append(clean_doc)
                    lines.append("")
                
                # 继承关系
                if class_info.bases:
                    bases_str = ", ".join(class_info.bases)
                    lines.append(f"**继承自**: `{bases_str}`")
                    lines.append("")
                
                # 类属性
                if class_info.attributes:
                    lines.append("#### 属性")
                    lines.append("")
                    for attr_name, attr_type in class_info.attributes:
                        if attr_type:
                            lines.append(f"- `{attr_name}` (`{attr_type}`)")
                        else:
                            lines.append(f"- `{attr_name}`")
                    lines.append("")
                
                # 方法
                if class_info.methods:
                    lines.append("#### 方法")
                    lines.append("")
                    
                    for method in class_info.methods:
                        # 跳过私有方法（可选）
                        if method.name.startswith("_"):
                            continue
                        
                        lines.append(f"##### {method.name}")
                        lines.append("")
                        
                        # 方法签名
                        sig_parts = []
                        if method.is_async:
                            sig_parts.append("async")
                        if method.is_static:
                            sig_parts.append("@staticmethod")
                        if method.is_classmethod:
                            sig_parts.append("@classmethod")
                        
                        sig_parts.append(f"def {method.name}(")
                        args_str = []
                        for arg_name, arg_type in method.args:
                            if arg_type:
                                args_str.append(f"{arg_name}: {arg_type}")
                            else:
                                args_str.append(arg_name)
                        sig_parts.append(", ".join(args_str))
                        sig_parts.append(")")
                        
                        if method.returns:
                            sig_parts.append(f" -> {method.returns}")
                        
                        lines.append("```python")
                        lines.append(" ".join(sig_parts))
                        lines.append("```")
                        lines.append("")
                        
                        # 方法 docstring
                        if method.docstring:
                            clean_doc = self._clean_docstring(method.docstring)
                            lines.append(clean_doc)
                            lines.append("")
                            
                            # 参数说明（Sphinx 风格优先）
                            params = self.parser.parse_docstring_params(method.docstring)
                            if params:
                                lines.append("**参数**:")
                                lines.append("")
                                for param_name, param_desc in params.items():
                                    lines.append(f"- `{param_name}`: {param_desc}")
                                lines.append("")
                            
                            # 返回值说明（Sphinx 风格优先）
                            returns = self.parser.parse_docstring_returns(method.docstring)
                            if returns:
                                lines.append(f"**返回值**: {returns}")
                                lines.append("")
                            
                            # 异常说明（Sphinx 风格: :raises Exception: description）
                            raises = self.parser.parse_docstring_raises(method.docstring)
                            if raises:
                                lines.append("**异常**:")
                                lines.append("")
                                for exc_type, exc_desc in raises.items():
                                    lines.append(f"- `{exc_type}`: {exc_desc}")
                                lines.append("")
        
        # 模块级别函数
        if module_info.functions:
            lines.append("## 函数")
            lines.append("")
            
            for func in module_info.functions:
                if func.name.startswith("_"):
                    continue
                
                lines.append(f"### {func.name}")
                lines.append("")
                
                # 函数签名
                sig_parts = []
                if func.is_async:
                    sig_parts.append("async")
                sig_parts.append(f"def {func.name}(")
                args_str = []
                for arg_name, arg_type in func.args:
                    if arg_type:
                        args_str.append(f"{arg_name}: {arg_type}")
                    else:
                        args_str.append(arg_name)
                sig_parts.append(", ".join(args_str))
                sig_parts.append(")")
                
                if func.returns:
                    sig_parts.append(f" -> {func.returns}")
                
                lines.append("```python")
                lines.append(" ".join(sig_parts))
                lines.append("```")
                lines.append("")
                
                # 函数 docstring
                if func.docstring:
                    clean_doc = self._clean_docstring(func.docstring)
                    lines.append(clean_doc)
                    lines.append("")
                    
                    # 参数说明（Sphinx 风格优先）
                    params = self.parser.parse_docstring_params(func.docstring)
                    if params:
                        lines.append("**参数**:")
                        lines.append("")
                        for param_name, param_desc in params.items():
                            lines.append(f"- `{param_name}`: {param_desc}")
                        lines.append("")
                    
                    # 返回值说明（Sphinx 风格优先）
                    returns = self.parser.parse_docstring_returns(func.docstring)
                    if returns:
                        lines.append(f"**返回值**: {returns}")
                        lines.append("")
                    
                    # 异常说明（Sphinx 风格）
                    raises = self.parser.parse_docstring_raises(func.docstring)
                    if raises:
                        lines.append("**异常**:")
                        lines.append("")
                        for exc_type, exc_desc in raises.items():
                            lines.append(f"- `{exc_type}`: {exc_desc}")
                        lines.append("")
        
        return "\n".join(lines)
    
    def _clean_docstring(self, docstring: str) -> str:
        """清理 docstring，移除注释格式"""
        # 移除 # @Time, # @User 等注释格式
        lines = docstring.split('\n')
        cleaned = []
        for line in lines:
            # 跳过 # @ 开头的注释行
            if re.match(r'^\s*#\s*@', line):
                continue
            cleaned.append(line)
        return '\n'.join(cleaned).strip()


def convert_file(input_file: Path, output_file: Path, base_path: Path):
    """转换单个文件"""
    parser = CodeParser()
    generator = MarkdownGenerator(parser)
    
    print(f"解析: {input_file}")
    module_info = parser.parse_file(input_file)
    
    print(f"生成: {output_file}")
    markdown_content = generator.generate(module_info, input_file, base_path)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"[OK] 完成: {output_file}")


def convert_directory(input_dir: Path, output_dir: Path, base_path: Path):
    """批量转换目录"""
    python_files = list(input_dir.rglob("*.py"))
    
    for py_file in python_files:
        if "__pycache__" in str(py_file):
            continue
        if py_file.name == "__init__.py":
            continue
        
        # 计算相对路径
        rel_path = py_file.relative_to(input_dir)
        output_file = output_dir / rel_path.with_suffix(".md")
        
        convert_file(py_file, output_file, base_path)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="将 Python 代码转换为 Markdown 文档")
    parser.add_argument("input", type=str, help="输入文件或目录路径")
    parser.add_argument("-o", "--output", type=str, help="输出文件或目录路径")
    parser.add_argument("-b", "--base", type=str, help="基础路径（用于计算模块路径）")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    base_path = Path(args.base) if args.base else input_path.parent
    
    if not input_path.exists():
        print(f"错误: 路径不存在 {input_path}")
        return
    
    if input_path.is_file():
        # 单个文件
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = input_path.with_suffix(".md")
        convert_file(input_path, output_path, base_path)
    else:
        # 目录
        if args.output:
            output_dir = Path(args.output)
        else:
            output_dir = input_path.parent / f"{input_path.name}_docs"
        convert_directory(input_path, output_dir, base_path)
        print(f"\n[OK] 批量转换完成，输出目录: {output_dir}")


if __name__ == "__main__":
    # ========== PyCharm 直接运行配置 ==========
    # 在 PyCharm 中可以直接运行此脚本，无需命令行参数
    # 修改下面的配置即可
    
    # 配置：要转换的源代码目录或文件
    # 选项1: 转换整个项目目录
    CONVERT_NTRT_PROJECT = False     # 是否转换 NTRT 项目
    CONVERT_RCSB_PDB_PROJECT = True  # 是否转换 RCSB PDB 项目（输出到 ntrt）
    
    # 选项2: 转换单个文件（如果设置了，会优先使用）
    CONVERT_SINGLE_FILE = None       # 例如: "code_liu/NTRT/data_cleaner.py"
    
    # 输出目录配置
    OUTPUT_TO_DOCS = True            # 是否输出到 docs 目录
    OUTPUT_SUBDIR = "generated"      # docs 下的子目录
    
    # ========== 自动执行 ==========
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    docs_dir = script_dir.parent / "docs"
    
    import sys
    
    # 如果提供了命令行参数，使用命令行模式
    if len(sys.argv) > 1:
        main()
    else:
        # PyCharm 直接运行模式
        print("=" * 60)
        print("PyCharm 直接运行模式")
        print("=" * 60)
        print()
        
        # 转换单个文件
        if CONVERT_SINGLE_FILE:
            input_file = project_root / CONVERT_SINGLE_FILE
            if input_file.exists():
                if OUTPUT_TO_DOCS:
                    output_file = docs_dir / OUTPUT_SUBDIR / input_file.stem / f"{input_file.stem}.md"
                else:
                    output_file = input_file.with_suffix(".md")
                
                print(f"转换单个文件: {input_file}")
                convert_file(input_file, output_file, project_root)
            else:
                print(f"错误: 文件不存在 {input_file}")
        
        # 转换 NTRT 项目
        elif CONVERT_NTRT_PROJECT:
            ntrt_dir = project_root / "code_liu" / "NTRT"
            if ntrt_dir.exists():
                if OUTPUT_TO_DOCS:
                    output_dir = docs_dir / OUTPUT_SUBDIR / "NTRT"
                else:
                    output_dir = project_root / "code_liu" / "NTRT_docs"
                
                print(f"转换 NTRT 项目: {ntrt_dir}")
                print(f"输出目录: {output_dir}")
                print()
                convert_directory(ntrt_dir, output_dir, project_root / "code_liu")
            else:
                print(f"警告: NTRT 项目目录不存在 {ntrt_dir}")
        
        # 转换 RCSB PDB 项目（输出到 ntrt 目录）
        if CONVERT_RCSB_PDB_PROJECT:
            rcsb_dir = project_root / "code_liu" / "RCSB_PDB" / "src"
            if rcsb_dir.exists():
                if OUTPUT_TO_DOCS:
                    # 输出到 ntrt/generated 目录
                    output_dir = docs_dir / "projects" / "ntrt" / "generated"
                else:
                    output_dir = project_root / "code_liu" / "RCSB_PDB_docs"
                
                print()
                print(f"转换 RCSB PDB 项目: {rcsb_dir}")
                print(f"输出目录: {output_dir}")
                print()
                convert_directory(rcsb_dir, output_dir, project_root / "code_liu")
            else:
                print(f"警告: RCSB PDB 项目目录不存在 {rcsb_dir}")
        
        print()
        print("=" * 60)
        print("转换完成！")
        print("=" * 60)
        print()
        print("提示：")
        print("- 修改脚本顶部的配置可以改变转换目标")
        print("- 设置 CONVERT_SINGLE_FILE 可以转换单个文件")
        print("- 设置 CONVERT_NTRT_PROJECT = False 可以跳过 NTRT 项目")

