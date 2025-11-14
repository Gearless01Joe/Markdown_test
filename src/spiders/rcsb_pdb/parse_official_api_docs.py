# -*- coding: utf-8 -*-
"""
解析 RCSB PDB 官方 OpenAPI 文档

从官方 OpenAPI/Swagger JSON 文档中提取所有字段及其描述。
这个文档包含了所有 API 端点的完整定义和字段描述，比手动整理更准确。
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Set


def extract_field_descriptions(schema: Dict[str, Any], prefix: str = "", descriptions: Dict[str, str] = None) -> Dict[str, str]:
    """递归提取 schema 中所有字段的描述"""
    if descriptions is None:
        descriptions = {}
    
    if not isinstance(schema, dict):
        return descriptions
    
    # 如果是 $ref，需要解析引用（这里简化处理，只记录字段名）
    if "$ref" in schema:
        ref_path = schema["$ref"].replace("#/components/schemas/", "")
        # 记录引用关系，但不深入解析（避免循环引用）
        if prefix:
            descriptions[f"{prefix}_ref_{ref_path}"] = f"引用类型: {ref_path}"
        return descriptions
    
    # 提取当前字段的描述
    if "description" in schema and prefix:
        descriptions[prefix] = schema["description"]
    
    # 处理 properties（对象属性）
    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            full_name = f"{prefix}.{prop_name}" if prefix else prop_name
            extract_field_descriptions(prop_schema, full_name, descriptions)
    
    # 处理 items（数组元素）
    if "items" in schema:
        items_schema = schema["items"]
        if isinstance(items_schema, dict):
            # 如果是对象数组，提取对象属性
            if "properties" in items_schema:
                for prop_name, prop_schema in items_schema["properties"].items():
                    full_name = f"{prefix}.{prop_name}" if prefix else prop_name
                    extract_field_descriptions(prop_schema, full_name, descriptions)
            elif "$ref" in items_schema:
                ref_path = items_schema["$ref"].replace("#/components/schemas/", "")
                descriptions[f"{prefix}_item_ref_{ref_path}"] = f"数组元素类型: {ref_path}"
    
    # 处理 allOf, anyOf, oneOf
    for key in ["allOf", "anyOf", "oneOf"]:
        if key in schema:
            for sub_schema in schema[key]:
                extract_field_descriptions(sub_schema, prefix, descriptions)
    
    return descriptions


def parse_openapi_doc(json_file: Path) -> Dict[str, Any]:
    """解析 OpenAPI 文档，提取所有字段描述"""
    print(f"正在解析 OpenAPI 文档: {json_file}")
    
    with json_file.open("r", encoding="utf-8") as f:
        doc = json.load(f)
    
    result = {
        "api_info": {
            "title": doc.get("info", {}).get("title"),
            "version": doc.get("info", {}).get("version"),
            "description": doc.get("info", {}).get("description"),
        },
        "paths": {},
        "schemas": {},
        "field_descriptions": {},
    }
    
    # 提取所有路径（API 端点）
    paths = doc.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method == "get":
                summary = details.get("summary", "")
                operation_id = details.get("operationId", "")
                tags = details.get("tags", [])
                
                # 提取响应 schema
                responses = details.get("responses", {})
                schema_ref = None
                for status, response in responses.items():
                    if status == "200":
                        content = response.get("content", {})
                        for content_type, content_schema in content.items():
                            if "schema" in content_schema:
                                schema = content_schema["schema"]
                                if "$ref" in schema:
                                    schema_ref = schema["$ref"].replace("#/components/schemas/", "")
                
                result["paths"][path] = {
                    "summary": summary,
                    "operation_id": operation_id,
                    "tags": tags,
                    "schema_ref": schema_ref,
                }
    
    # 提取所有 schema 定义
    components = doc.get("components", {})
    schemas = components.get("schemas", {})
    
    print(f"找到 {len(schemas)} 个 schema 定义")
    
    # 为每个 schema 提取字段描述
    for schema_name, schema_def in schemas.items():
        field_descriptions = extract_field_descriptions(schema_def, schema_name)
        result["schemas"][schema_name] = {
            "type": schema_def.get("type"),
            "description": schema_def.get("description"),
            "field_descriptions": field_descriptions,
        }
        result["field_descriptions"].update(field_descriptions)
    
    print(f"提取了 {len(result['field_descriptions'])} 个字段描述")
    
    return result


def generate_markdown_from_official_docs(parsed_data: Dict[str, Any]) -> str:
    """根据官方文档生成 Markdown 格式的字段列表"""
    lines = []
    
    lines.append("# RCSB PDB API 完整字段列表（来自官方 OpenAPI 文档）\n")
    lines.append(f"\n**API 版本**: {parsed_data['api_info']['version']}\n")
    lines.append(f"**文档标题**: {parsed_data['api_info']['title']}\n")
    lines.append(f"**描述**: {parsed_data['api_info']['description']}\n")
    lines.append("\n---\n")
    
    # 按 API 路径组织
    paths_by_tag = {}
    for path, path_info in parsed_data["paths"].items():
        tags = path_info.get("tags", ["Other"])
        tag = tags[0] if tags else "Other"
        if tag not in paths_by_tag:
            paths_by_tag[tag] = []
        paths_by_tag[tag].append((path, path_info))
    
    # 为每个 tag 生成文档
    for tag, path_list in sorted(paths_by_tag.items()):
        lines.append(f"\n## {tag}\n")
        
        for path, path_info in path_list:
            lines.append(f"\n### {path_info['summary']}\n")
            lines.append(f"**路径**: `{path}`\n")
            lines.append(f"**操作 ID**: `{path_info['operation_id']}`\n")
            
            schema_ref = path_info.get("schema_ref")
            if schema_ref:
                lines.append(f"**返回类型**: `{schema_ref}`\n")
                
                # 查找对应的 schema 字段
                schema_data = parsed_data["schemas"].get(schema_ref)
                if schema_data:
                    field_descriptions = schema_data.get("field_descriptions", {})
                    if field_descriptions:
                        lines.append("\n#### 字段列表\n\n")
                        # 按字段名排序
                        for field_name in sorted(field_descriptions.keys()):
                            description = field_descriptions[field_name]
                            # 简化字段名（去掉 schema 前缀）
                            display_name = field_name.replace(f"{schema_ref}.", "")
                            lines.append(f"- `{display_name}` - {description}\n")
            
            lines.append("\n---\n")
    
    return "".join(lines)


def main():
    """主函数"""
    print("=" * 80)
    print("RCSB PDB 官方 OpenAPI 文档解析工具")
    print("=" * 80)
    print()
    
    # 查找 OpenAPI 文档
    inhance_dir = Path(__file__).parent / "inhance"
    json_file = inhance_dir / "rcsb-restful-api-docs (1).json"
    
    if not json_file.exists():
        print(f"错误: 找不到 OpenAPI 文档: {json_file}")
        print("请确保文件存在")
        return
    
    # 解析文档
    parsed_data = parse_openapi_doc(json_file)
    
    # 保存解析结果
    output_dir = inhance_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存 JSON 格式的解析结果
    json_output = output_dir / "official_api_docs_parsed.json"
    with json_output.open("w", encoding="utf-8") as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] 解析结果已保存到: {json_output}")
    
    # 生成 Markdown 文档
    md_content = generate_markdown_from_official_docs(parsed_data)
    md_output = output_dir / "official_api_fields_complete.md"
    with md_output.open("w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[OK] Markdown 文档已保存到: {md_output}")
    
    # 生成字段描述字典（用于 explore_api_fields.py）
    field_desc_dict = {}
    for field_name, description in parsed_data["field_descriptions"].items():
        # 简化字段名（只取最后一部分）
        simple_name = field_name.split(".")[-1]
        if simple_name not in field_desc_dict or len(description) > len(field_desc_dict.get(simple_name, "")):
            field_desc_dict[simple_name] = description
    
    desc_dict_output = output_dir / "official_field_descriptions.json"
    with desc_dict_output.open("w", encoding="utf-8") as f:
        json.dump(field_desc_dict, f, ensure_ascii=False, indent=2)
    print(f"[OK] 字段描述字典已保存到: {desc_dict_output}")
    print(f"   共 {len(field_desc_dict)} 个字段描述")
    
    print("\n" + "=" * 80)
    print("完成！")
    print("=" * 80)
    print("\n提示: 可以使用生成的字段描述字典来更新 explore_api_fields.py 中的字段说明")


if __name__ == "__main__":
    main()

