# -*- coding: utf-8 -*-
"""
分析 rcsb_spider_plus.py 中所有字段及其在官方文档中的描述

提取所有字段，查找对应的 API 端点和字段描述
"""
import json
import re
from pathlib import Path
from typing import Dict, Any, List


def extract_fields_from_spider(spider_file: Path) -> Dict[str, Dict[str, Any]]:
    """从爬虫代码中提取所有字段及其使用的 API"""
    with spider_file.open("r", encoding="utf-8") as f:
        content = f.read()
    
    fields_info = {}
    
    # 1. GraphQL API 字段
    graphql_fields = {
        "Organism": {
            "api": "GraphQL API",
            "api_endpoint": "https://data.rcsb.org/graphql",
            "extraction_path": "entry.polymer_entities[].rcsb_entity_source_organism[].ncbi_scientific_name",
            "code_location": "extract_from_graphql -> _extract_polymer_data (line 503-506)"
        },
        "Expression_System": {
            "api": "GraphQL API",
            "api_endpoint": "https://data.rcsb.org/graphql",
            "extraction_path": "entry.polymer_entities[].rcsb_entity_host_organism[].ncbi_scientific_name",
            "code_location": "extract_from_graphql -> _extract_polymer_data (line 508-512)"
        },
        "Macromolecule": {
            "api": "GraphQL API",
            "api_endpoint": "https://data.rcsb.org/graphql",
            "extraction_path": "entry.polymer_entities[].rcsb_polymer_entity.pdbx_description + entity_poly.type + entity_poly.pdbx_strand_id",
            "code_location": "extract_from_graphql -> _extract_polymer_data (line 514-538)"
        },
        "Mutation": {
            "api": "GraphQL API",
            "api_endpoint": "https://data.rcsb.org/graphql",
            "extraction_path": "entry.polymer_entities[].rcsb_polymer_entity_feature[].name (where type='mutation')",
            "code_location": "extract_from_graphql -> _extract_polymer_data (line 540-546)"
        },
        "unique_Ligands": {
            "api": "GraphQL API",
            "api_endpoint": "https://data.rcsb.org/graphql",
            "extraction_path": "entry.nonpolymer_entities[].pdbx_entity_nonpoly.comp_id + name",
            "code_location": "extract_from_graphql -> _extract_nonpolymer_data (line 565-586)"
        }
    }
    
    # 2. Entry API 字段
    entry_fields = {
        "Title": {
            "api": "REST Entry API",
            "api_endpoint": "/rest/v1/core/entry/{entry_id}",
            "extraction_path": "struct.title",
            "code_location": "_extract_basic_info (line 611-612)"
        },
        "PDB_DOI": {
            "api": "REST Entry API",
            "api_endpoint": "/rest/v1/core/entry/{entry_id}",
            "extraction_path": "database2[].pdbx_doi",
            "code_location": "_extract_basic_info (line 614-619)"
        },
        "Classification": {
            "api": "REST Entry API",
            "api_endpoint": "/rest/v1/core/entry/{entry_id}",
            "extraction_path": "struct_keywords.pdbx_keywords",
            "code_location": "_extract_basic_info (line 621-623)"
        },
        "Deposited": {
            "api": "REST Entry API",
            "api_endpoint": "/rest/v1/core/entry/{entry_id}",
            "extraction_path": "rcsb_accession_info.deposit_date",
            "code_location": "_extract_basic_info (line 625-629)"
        },
        "Released": {
            "api": "REST Entry API",
            "api_endpoint": "/rest/v1/core/entry/{entry_id}",
            "extraction_path": "rcsb_accession_info.initial_release_date",
            "code_location": "_extract_basic_info (line 625-629)"
        },
        "Deposition_Author": {
            "api": "REST Entry API",
            "api_endpoint": "/rest/v1/core/entry/{entry_id}",
            "extraction_path": "audit_author[].name",
            "code_location": "_extract_basic_info (line 631-635)"
        },
        "PMID": {
            "api": "REST Entry API",
            "api_endpoint": "/rest/v1/core/entry/{entry_id}",
            "extraction_path": "citation[].pdbx_database_id_pub_med",
            "code_location": "_extract_basic_info (line 637-642)"
        },
        "Macromolecule_Content": {
            "api": "REST Entry API",
            "api_endpoint": "/rest/v1/core/entry/{entry_id}",
            "extraction_path": "rcsb_entry_info",
            "code_location": "_extract_macromolecule_content_extended (line 644-666)",
            "sub_fields": {
                "Total_Structure_Weight": "rcsb_entry_info.molecular_weight",
                "Atom_Count": "rcsb_entry_info.deposited_atom_count",
                "Modeled_Residue_Count": "rcsb_entry_info.deposited_modeled_polymer_monomer_count",
                "Deposited_Residue_Count": "rcsb_entry_info.deposited_polymer_monomer_count",
                "Unique_Protein_Chains": "rcsb_entry_info.polymer_entity_count",
                "Solvent_Atom_Count": "rcsb_entry_info.deposited_solvent_atom_count",
                "Model_Count": "rcsb_entry_info.deposited_model_count",
                "Polymer_Composition": "rcsb_entry_info.polymer_composition",
                "Nonpolymer_Entity_Count": "rcsb_entry_info.nonpolymer_entity_count"
            }
        },
        "Experimental_Data_Snapshot": {
            "api": "REST Entry API",
            "api_endpoint": "/rest/v1/core/entry/{entry_id}",
            "extraction_path": "exptl[] + refine[] + ...",
            "code_location": "_extract_experimental_data (line 668-691)",
            "sub_fields": {
                "Experimental_Method": "exptl[].method",
                "Resolution": "refine[].ls_dres_high or rcsb_entry_info.diffrn_resolution_high",
                "R-Value Work": "refine[].ls_rfactor_rwork",
                "R-Value Free": "refine[].ls_rfactor_rfree",
                "R-Value Observed": "refine[].ls_rfactor_obs",
                "Aggregation State": "em_experiment.aggregation_state",
                "Reconstruction Method": "em_experiment.reconstruction_method",
                "Conformers Calculated": "pdbx_nmr_ensemble.conformers_calculated_total_number",
                "Conformers Submitted": "pdbx_nmr_ensemble.conformers_submitted_total_number",
                "Selection Criteria": "pdbx_nmr_representative.selection_criteria"
            }
        }
    }
    
    # 3. Assembly API 字段
    assembly_fields = {
        "Global_Symmetry": {
            "api": "REST Assembly API",
            "api_endpoint": "/rest/v1/core/assembly/{entry_id}/{assembly_id}",
            "extraction_path": "rcsb_struct_symmetry[].type + symbol (where kind='Global Symmetry')",
            "code_location": "extract_from_assembly_api (line 799-805)"
        },
        "Global_Stoichiometry": {
            "api": "REST Assembly API",
            "api_endpoint": "/rest/v1/core/assembly/{entry_id}/{assembly_id}",
            "extraction_path": "rcsb_struct_symmetry[].oligomeric_state + stoichiometry (where kind='Global Symmetry')",
            "code_location": "extract_from_assembly_api (line 807-813)"
        }
    }
    
    # 合并所有字段
    fields_info.update(graphql_fields)
    fields_info.update(entry_fields)
    fields_info.update(assembly_fields)
    
    return fields_info


def find_field_description_in_docs(field_path: str, official_docs: Dict[str, Any], schema_name: str = None) -> str:
    """在官方文档中查找字段描述"""
    field_descriptions = official_docs.get("field_descriptions", {})
    
    # ========== 1. 处理组合字段（包含 + 符号）==========
    if "+" in field_path:
        parts = [p.strip() for p in field_path.split("+")]
        descriptions = []
        for part in parts:
            # 递归查找每个部分的描述
            part_desc = find_field_description_in_docs(part, official_docs, schema_name)
            if part_desc:
                # 提取简短描述（取第一句）
                short_desc = part_desc.split(".")[0] if "." in part_desc else part_desc
                descriptions.append(f"{part.split('.')[-1]} ({short_desc})")
        if descriptions:
            return f"Combined field: {' + '.join(descriptions)}"
    
    # ========== 2. 处理聚合字段（包含 .*）==========
    if ".*" in field_path:
        base_path = field_path.replace(".*", "").replace("[]", "")
        # 查找对应的 schema
        schemas = official_docs.get("schemas", {})
        if schema_name and schema_name in schemas:
            schema_desc = schemas[schema_name].get("description")
            if schema_desc:
                return f"Aggregate field from {base_path}: {schema_desc}"
        # 尝试查找基础路径的描述
        base_desc = find_field_description_in_docs(base_path, official_docs, schema_name)
        if base_desc:
            return f"Aggregate field containing all fields from {base_path}: {base_desc}"
        return f"Aggregate field containing all fields from {base_path}"
    
    # ========== 3. GraphQL 到 REST 的路径映射 ==========
    graphql_to_rest_mapping = {
        "rcsb_entity_source_organism": {
            "ncbi_scientific_name": "RcsbEntitySourceOrganism.ncbi_scientific_name"
        },
        "rcsb_entity_host_organism": {
            "ncbi_scientific_name": "RcsbEntityHostOrganism.ncbi_scientific_name"
        },
        "rcsb_polymer_entity": {
            "pdbx_description": "RcsbPolymerEntity.pdbx_description",
            "formula_weight": "RcsbPolymerEntity.formula_weight"
        },
        "entity_poly": {
            "type": "EntityPoly.type",
            "pdbx_strand_id": "EntityPoly.pdbx_strand_id"
        },
        "pdbx_entity_nonpoly": {
            "comp_id": "PdbxEntityNonpoly.comp_id",
            "name": "PdbxEntityNonpoly.name"
        }
    }
    
    # 尝试 GraphQL 路径映射
    for graphql_key, rest_mapping in graphql_to_rest_mapping.items():
        if graphql_key in field_path:
            for graphql_field, rest_path in rest_mapping.items():
                if graphql_field in field_path:
                    if rest_path in field_descriptions:
                        return field_descriptions[rest_path]
    
    # ========== 4. 清理字段路径（移除数组标记和条件）==========
    clean_path = field_path.split("[")[0].split("(")[0].strip()
    parts = clean_path.split(".")
    
    # ========== 5. 尝试完整路径匹配（包含 schema 前缀）==========
    if schema_name and schema_name != "GraphQL (no fixed schema)":
        full_path_with_schema = f"{schema_name}.{'.'.join(parts)}"
        if full_path_with_schema in field_descriptions:
            return field_descriptions[full_path_with_schema]
    
    # ========== 6. 尝试直接完整路径匹配 ==========
    full_path = ".".join(parts)
    if full_path in field_descriptions:
        return field_descriptions[full_path]
    
    # ========== 7. 大小写不敏感匹配 ==========
    field_name = parts[-1]
    field_lower = field_name.lower()
    
    # 尝试大小写不敏感匹配
    for key, desc in field_descriptions.items():
        key_lower = key.lower()
        # 精确匹配（忽略大小写）
        if key_lower == field_lower or key_lower.endswith(f".{field_lower}"):
            return desc
        # 匹配最后一部分（忽略大小写）
        if key_lower.endswith(f".{field_lower}") or key_lower == field_lower:
            return desc
        # 特殊处理：doi 字段的大小写变体
        if "doi" in field_lower and "doi" in key_lower:
            # 检查是否是同一个字段的不同大小写形式
            key_base = key.split(".")[-1].lower() if "." in key else key.lower()
            if key_base.replace("_", "") == field_lower.replace("_", ""):
                return desc
    
    # ========== 8. 特殊字段映射（根据实际 API 字段路径）==========
    field_mappings = {
        "comp_id": "PdbxEntityNonpoly.comp_id",
        "name": "PdbxEntityNonpoly.name",  # 对于 nonpolymer
        "title": "Struct.title",
        "pdbx_doi": "Database2.pdbx_DOI",  # 注意大小写
        "pdbx_keywords": "StructKeywords.pdbx_keywords",
        "deposit_date": "RcsbAccessionInfo.deposit_date",
        "initial_release_date": "RcsbAccessionInfo.initial_release_date",
        "ncbi_scientific_name": "RcsbEntitySourceOrganism.ncbi_scientific_name",
        "pdbx_description": "RcsbPolymerEntity.pdbx_description",
        "formula_weight": "RcsbPolymerEntity.formula_weight",
        "pdbx_strand_id": "EntityPoly.pdbx_strand_id",
        "pdbx_database_id_pub_med": "Citation.pdbx_database_id_PubMed",
        "ls_rfactor_rwork": "Refine.ls_rfactor_rwork",
        "ls_rfactor_rfree": "Refine.ls_rfactor_rfree",
        "ls_rfactor_obs": "Refine.ls_rfactor_obs",
        "ls_dres_high": "Refine.ls_dres_high",
    }
    
    # 特殊处理：database2 路径中的 pdbx_doi
    if "database2" in field_path.lower() and "doi" in field_path.lower():
        if "Database2.pdbx_DOI" in field_descriptions:
            return field_descriptions["Database2.pdbx_DOI"]
        # 尝试大小写变体
        for key, desc in field_descriptions.items():
            if "database2" in key.lower() and "doi" in key.lower():
                return desc
    
    # 根据字段路径的特殊处理
    if "polymer_entity_feature" in field_path.lower() and "name" in field_path.lower():
        # Mutation 字段来自 rcsb_polymer_entity_feature.name
        if "RcsbPolymerEntityFeature.name" in field_descriptions:
            return field_descriptions["RcsbPolymerEntityFeature.name"]
    
    if "nonpolymer" in field_path.lower() or "pdbx_entity_nonpoly" in field_path.lower():
        # unique_Ligands 字段
        if "comp_id" in field_path.lower():
            if "PdbxEntityNonpoly.comp_id" in field_descriptions:
                return field_descriptions["PdbxEntityNonpoly.comp_id"]
        if "name" in field_path.lower() and "comp_id" not in field_path.lower():
            if "PdbxEntityNonpoly.name" in field_descriptions:
                return field_descriptions["PdbxEntityNonpoly.name"]
    
    if field_name in field_mappings:
        mapped_key = field_mappings[field_name]
        if mapped_key in field_descriptions:
            return field_descriptions[mapped_key]
    
    # ========== 9. 尝试匹配最后一部分（字段名），优先匹配带 schema 的 ==========
    if schema_name and schema_name != "GraphQL (no fixed schema)":
        schema_field_key = f"{schema_name}.{field_name}"
        if schema_field_key in field_descriptions:
            return field_descriptions[schema_field_key]
    
    # 再尝试匹配以字段名结尾的
    for key, desc in field_descriptions.items():
        if key.endswith(f".{field_name}"):
            return desc
    
    # ========== 10. 尝试模糊匹配（包含字段名）==========
    for key, desc in field_descriptions.items():
        if field_name.lower() in key.lower() and len(field_name) > 3:
            # 确保是完整单词匹配
            if f".{field_name}" in key or key.endswith(field_name):
                return desc
    
    return None


def find_schema_for_field(field_path: str, api_endpoint: str, official_docs: Dict[str, Any]) -> str:
    """根据 API 端点查找对应的 schema"""
    paths = official_docs.get("paths", {})
    
    # 查找匹配的路径
    for path, path_info in paths.items():
        if api_endpoint.replace("https://data.rcsb.org", "") in path or path in api_endpoint:
            schema_ref = path_info.get("schema_ref")
            if schema_ref:
                return schema_ref
    
    # 根据 API 端点推断 schema
    if "entry" in api_endpoint.lower():
        return "CoreEntry"
    elif "assembly" in api_endpoint.lower():
        return "CoreAssembly"
    elif "graphql" in api_endpoint.lower():
        return "GraphQL (no fixed schema)"
    
    return None


def build_field_details(fields_info: Dict[str, Dict[str, Any]], official_docs: Dict[str, Any]) -> Dict[str, Any]:
    """构建字段详细信息"""
    result = {}
    
    for field_name, field_info in fields_info.items():
        field_detail = {
            "field_name": field_name,
            "api": field_info["api"],
            "api_endpoint": field_info["api_endpoint"],
            "extraction_path": field_info["extraction_path"],
            "code_location": field_info.get("code_location", ""),
            "schema": find_schema_for_field(
                field_info["extraction_path"],
                field_info["api_endpoint"],
                official_docs
            ),
            "description": None,
            "sub_fields": {}
        }
        
        # 查找字段描述
        description = find_field_description_in_docs(
            field_info["extraction_path"], 
            official_docs,
            schema_name=field_detail["schema"]
        )
        if description:
            field_detail["description"] = description
        
        # 处理子字段（如 Macromolecule_Content 的子字段）
        if "sub_fields" in field_info:
            for sub_field_name, sub_field_path in field_info["sub_fields"].items():
                sub_description = find_field_description_in_docs(
                    sub_field_path, 
                    official_docs,
                    schema_name=field_detail["schema"]
                )
                field_detail["sub_fields"][sub_field_name] = {
                    "extraction_path": sub_field_path,
                    "description": sub_description
                }
        
        result[field_name] = field_detail
    
    return result


def main():
    """主函数"""
    print("=" * 80)
    print("分析 rcsb_spider_plus.py 中的字段及其官方文档描述")
    print("=" * 80)
    print()
    
    # 文件路径
    spider_file = Path(__file__).parent / "rcsb_spider_plus.py"
    docs_file = Path(__file__).parent / "inhance" / "official_api_docs_parsed.json"
    output_file = Path(__file__).parent / "inhance" / "now_details.json"
    
    # 读取官方文档
    print(f"正在读取官方文档: {docs_file}")
    with docs_file.open("r", encoding="utf-8") as f:
        official_docs = json.load(f)
    print(f"[OK] 已加载官方文档（{len(official_docs.get('schemas', {}))} 个 schemas）")
    print()
    
    # 提取字段信息
    print("正在分析爬虫代码中的字段...")
    fields_info = extract_fields_from_spider(spider_file)
    print(f"[OK] 找到 {len(fields_info)} 个字段")
    print()
    
    # 构建详细信息
    print("正在查找字段描述...")
    field_details = build_field_details(fields_info, official_docs)
    print(f"[OK] 已构建字段详细信息")
    print()
    
    # 统计信息
    api_counts = {}
    for field_name, detail in field_details.items():
        api = detail["api"]
        api_counts[api] = api_counts.get(api, 0) + 1
    
    print("字段统计：")
    for api, count in api_counts.items():
        print(f"  {api}: {count} 个字段")
    print()
    
    # 保存结果
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(field_details, f, ensure_ascii=False, indent=2)
    print(f"[OK] 结果已保存到: {output_file}")
    print()
    print("=" * 80)
    print("完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()

