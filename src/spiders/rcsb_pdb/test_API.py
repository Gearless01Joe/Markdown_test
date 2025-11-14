# -*- coding: utf-8 -*-
"""
RCSB PDB API 测试爬虫 - 根据 now_details.json 自动提取字段

根据 now_details.json 中定义的字段和提取路径，自动从相应 API 获取数据并保存。

配置：
    PDB_ID = "7IAQ"  # 要查询的 PDB ID
    OUTPUT_FILENAME = "want_know.json"  # 输出文件名（保存在 inhance 目录下）
"""
import json
import re
from pathlib import Path
import scrapy


class RcsbApiAttributeDemoSpider(scrapy.Spider):
    """根据 now_details.json 自动提取字段的爬虫"""

    name = "rcsb_api_test"
    allowed_domains = ["data.rcsb.org"]
    start_urls = ["https://www.rcsb.org/"]

    # ========== 配置区域 ==========
    PDB_ID = "7IAQ"  # 要查询的 PDB ID
    OUTPUT_FILENAME = "want_know.json"  # 输出文件名
    # =============================

    # API 端点常量
    GRAPHQL_URL = "https://data.rcsb.org/graphql"
    ENTRY_API_BASE = "https://data.rcsb.org/rest/v1/core/entry"
    ASSEMBLY_API_BASE = "https://data.rcsb.org/rest/v1/core/assembly"
    POLYMER_ENTITY_API_BASE = "https://data.rcsb.org/rest/v1/core/polymer_entity"

    custom_settings = {
        "ITEM_PIPELINES": {},
        "DOWNLOAD_DELAY": 0.2,
        "LOG_LEVEL": "INFO",
    }

    def __init__(self, pdb_id=None, output_filename=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_id = (pdb_id or self.PDB_ID).upper()
        self.output_filename = output_filename or self.OUTPUT_FILENAME
        
        # 设置输出路径
        inhance_dir = Path(__file__).resolve().parent / "inhance"
        inhance_dir.mkdir(parents=True, exist_ok=True)
        self.output_path = inhance_dir / self.output_filename
        
        # 读取字段定义
        now_details_path = inhance_dir / "now_details.json"
        if now_details_path.exists():
            with now_details_path.open("r", encoding="utf-8") as f:
                self.field_definitions = json.load(f)
        else:
            self.logger.error(f"未找到字段定义文件: {now_details_path}")
            self.field_definitions = {}
        
        # 初始化结果字典
        self.result = {}

    def parse(self, response):
        """入口：根据字段定义调用相应的 API"""
        # 按 API 类型分组字段
        graphql_fields = []
        entry_api_fields = []
        assembly_api_fields = []
        polymer_entity_fields = []
        
        for field_name, field_def in self.field_definitions.items():
            api_type = field_def.get("api", "")
            if "GraphQL" in api_type:
                graphql_fields.append((field_name, field_def))
            elif "REST Entry API" in api_type:
                entry_api_fields.append((field_name, field_def))
            elif "REST Assembly API" in api_type:
                assembly_api_fields.append((field_name, field_def))
            elif "REST Polymer Entity API" in api_type:
                polymer_entity_fields.append((field_name, field_def))
        
        # 先调用 GraphQL API（如果需要）
        if graphql_fields:
            yield from self._request_graphql(graphql_fields)
        # 调用 Entry API（如果需要）
        elif entry_api_fields:
            yield from self._request_entry_api(entry_api_fields)
        # 如果没有 GraphQL 和 Entry，直接调用 Assembly
        elif assembly_api_fields:
            yield from self._request_assembly_api(assembly_api_fields)
        else:
            self.logger.warning("没有找到需要提取的字段")
            yield from self._save_result()

    def _request_graphql(self, graphql_fields):
        """请求 GraphQL API"""
        # 构建 GraphQL 查询，包含所有需要的字段
        query_fields = []
        for field_name, field_def in graphql_fields:
            extraction_path = field_def.get("extraction_path", "")
            # 从提取路径中提取需要查询的字段
            query_fields.extend(self._extract_graphql_fields_from_path(extraction_path))
        
        # 去重并构建查询
        unique_fields = list(set(query_fields))
        query = self._build_graphql_query(unique_fields)
        
        graphql_query = {"query": query}
        
        yield scrapy.Request(
            url=self.GRAPHQL_URL,
            method="POST",
            body=json.dumps(graphql_query),
            headers={"Content-Type": "application/json"},
            callback=self.parse_graphql,
            meta={"graphql_fields": graphql_fields},
            dont_filter=True,
        )

    def _extract_graphql_fields_from_path(self, path):
        """从提取路径中提取 GraphQL 字段"""
        fields = []
        # 解析路径，提取字段名
        # 例如: entry.polymer_entities[].rcsb_entity_source_organism[].ncbi_scientific_name
        # 需要查询: polymer_entities { rcsb_entity_source_organism { ncbi_scientific_name } }
        
        # 简化处理：提取主要路径
        if "polymer_entities" in path:
            if "rcsb_entity_source_organism" in path:
                fields.append("polymer_entities.rcsb_entity_source_organism")
            if "rcsb_entity_host_organism" in path:
                fields.append("polymer_entities.rcsb_entity_host_organism")
            if "rcsb_polymer_entity" in path:
                fields.append("polymer_entities.rcsb_polymer_entity")
            if "entity_poly" in path:
                fields.append("polymer_entities.entity_poly")
            if "rcsb_polymer_entity_feature" in path:
                fields.append("polymer_entities.rcsb_polymer_entity_feature")
        
        if "nonpolymer_entities" in path:
            if "pdbx_entity_nonpoly" in path:
                fields.append("nonpolymer_entities.pdbx_entity_nonpoly")
        
        return fields

    def _build_graphql_query(self, fields):
        """构建 GraphQL 查询 - 提取完整的数据结构"""
        # 构建完整的查询结构，提取所有可能的字段
        query_parts = []
        
        if any("polymer_entities" in f for f in fields):
            polymer_query = """
                polymer_entities {
                  rcsb_id
                  entity_poly {
                    type
                    pdbx_strand_id
                    pdbx_seq_one_letter_code
                    pdbx_seq_one_letter_code_can
                    nstd_linkage
                    nstd_monomer
                  }
                  rcsb_polymer_entity {
                    pdbx_description
                    formula_weight
                    pdbx_number_of_molecules
                    rcsb_multiple_source_flag
                    rcsb_source_part_count
                    rcsb_source_taxonomy_count
                    src_method
                    rcsb_macromolecular_names_combined {
                      name
                      provenance_code
                      provenance_source
                    }
                    rcsb_polymer_name_combined {
                      names
                      provenance_source
                    }
                  }
                  rcsb_entity_source_organism {
                    beg_seq_num
                    end_seq_num
                    ncbi_common_names
                    ncbi_parent_scientific_name
                    ncbi_scientific_name
                    ncbi_taxonomy_id
                    pdbx_src_id
                    provenance_source
                    scientific_name
                    source_type
                    taxonomy_lineage {
                      depth
                      id
                      name
                    }
                    rcsb_gene_name {
                      provenance_source
                      value
                    }
                  }
                  rcsb_entity_host_organism {
                    beg_seq_num
                    end_seq_num
                    ncbi_common_names
                    ncbi_parent_scientific_name
                    ncbi_scientific_name
                    ncbi_taxonomy_id
                    pdbx_src_id
                    provenance_source
                    scientific_name
                    taxonomy_lineage {
                      depth
                      id
                      name
                    }
                  }
                  rcsb_polymer_entity_feature {
                    type
                    name
                    description
                    provenance_source
                    feature_id
                    assignment_version
                    feature_positions {
                      beg_seq_id
                      end_seq_id
                      beg_comp_id
                      value
                    }
                  }
                }
            """
            query_parts.append(polymer_query)
        
        if any("nonpolymer_entities" in f for f in fields):
            nonpolymer_query = """
                nonpolymer_entities {
                  rcsb_id
                  pdbx_entity_nonpoly {
                    comp_id
                    name
                  }
                }
            """
            query_parts.append(nonpolymer_query)
        
        query = f"""
        {{
          entry(entry_id: "{self.target_id}") {{
            {''.join(query_parts)}
          }}
        }}
        """
        return query

    def parse_graphql(self, response):
        """解析 GraphQL 响应 - 提取完整的数据结构"""
        try:
            graphql_payload = response.json()
        except Exception as exc:
            self.logger.warning("GraphQL 响应解析失败: %s", exc)
            graphql_payload = {}
        
        errors = graphql_payload.get("errors")
        if errors:
            messages = "; ".join(error.get("message", "") for error in errors)
            self.logger.warning("GraphQL 返回错误: %s", messages)
            # 即使有错误，也继续处理（可能部分数据可用）
        
        data = graphql_payload.get("data") or {}
        entry = data.get("entry") or {}
        
        if not entry:
            self.logger.warning("GraphQL 未返回 entry 数据")
        
        # 提取完整的 polymer_entities 数据
        if "polymer_entities" in entry and entry["polymer_entities"]:
            polymer_entities = entry["polymer_entities"]
            # 提取第一个 entity 的完整数据
            if polymer_entities:
                first_entity = polymer_entities[0]
                
                # 提取 entity_poly
                if "entity_poly" in first_entity:
                    self.result["entity_poly"] = first_entity["entity_poly"]
                
                # 提取 rcsb_entity_source_organism
                if "rcsb_entity_source_organism" in first_entity:
                    self.result["rcsb_entity_source_organism"] = first_entity["rcsb_entity_source_organism"]
                
                # 提取 rcsb_entity_host_organism
                if "rcsb_entity_host_organism" in first_entity:
                    self.result["rcsb_entity_host_organism"] = first_entity["rcsb_entity_host_organism"]
                
                # 提取 rcsb_polymer_entity
                if "rcsb_polymer_entity" in first_entity:
                    self.result["rcsb_polymer_entity"] = first_entity["rcsb_polymer_entity"]
                
                # 提取 rcsb_polymer_entity_feature
                if "rcsb_polymer_entity_feature" in first_entity:
                    self.result["rcsb_polymer_entity_feature"] = first_entity["rcsb_polymer_entity_feature"]
        
        # 提取 nonpolymer_entities 数据
        if "nonpolymer_entities" in entry and entry["nonpolymer_entities"]:
            # 这里通常不需要完整数据，但可以保留
            pass
        
        self.logger.info(f"GraphQL 提取完成，已提取 {len(self.result)} 个字段")
        
        # 继续处理其他 API
        entry_api_fields = []
        assembly_api_fields = []
        polymer_entity_fields = []
        
        for field_name, field_def in self.field_definitions.items():
            api_type = field_def.get("api", "")
            if "REST Entry API" in api_type:
                entry_api_fields.append((field_name, field_def))
            elif "REST Assembly API" in api_type:
                assembly_api_fields.append((field_name, field_def))
            elif "REST Polymer Entity API" in api_type:
                polymer_entity_fields.append((field_name, field_def))
        
        if entry_api_fields:
            yield from self._request_entry_api(entry_api_fields)
        elif assembly_api_fields:
            yield from self._request_assembly_api(assembly_api_fields)
        else:
            yield from self._save_result()

    def _request_entry_api(self, entry_api_fields):
        """请求 Entry API"""
        entry_url = f"{self.ENTRY_API_BASE}/{self.target_id}"
        yield scrapy.Request(
            url=entry_url,
            callback=self.parse_entry_api,
            meta={"entry_api_fields": entry_api_fields},
            dont_filter=True,
        )

    def parse_entry_api(self, response):
        """解析 Entry API 响应 - 提取完整的数据结构"""
        try:
            entry_data = response.json()
        except Exception as exc:
            self.logger.warning("Entry API 响应解析失败: %s", exc)
            entry_data = {}
        
        # 提取所有相关的完整数据结构
        # 根据 now_details.json 中的字段定义，提取完整对象
        
        # 提取 rcsb_entry_info（Macromolecule_Content）
        if "rcsb_entry_info" in entry_data:
            self.result["rcsb_entry_info"] = entry_data["rcsb_entry_info"]
        
        # 提取实验相关数据（Experimental_Data_Snapshot）
        if "exptl" in entry_data:
            self.result["exptl"] = entry_data["exptl"]
        if "refine" in entry_data:
            self.result["refine"] = entry_data["refine"]
        if "em_experiment" in entry_data:
            self.result["em_experiment"] = entry_data["em_experiment"]
        if "pdbx_nmr_ensemble" in entry_data:
            self.result["pdbx_nmr_ensemble"] = entry_data["pdbx_nmr_ensemble"]
        if "pdbx_nmr_representative" in entry_data:
            self.result["pdbx_nmr_representative"] = entry_data["pdbx_nmr_representative"]
        
        # 提取其他基本字段
        if "struct" in entry_data:
            self.result["struct"] = entry_data["struct"]
        if "struct_keywords" in entry_data:
            self.result["struct_keywords"] = entry_data["struct_keywords"]
        if "rcsb_accession_info" in entry_data:
            self.result["rcsb_accession_info"] = entry_data["rcsb_accession_info"]
        if "citation" in entry_data:
            self.result["citation"] = entry_data["citation"]
        if "database_2" in entry_data:
            self.result["database_2"] = entry_data["database_2"]
        if "audit_author" in entry_data:
            self.result["audit_author"] = entry_data["audit_author"]
        
        # 提取完整的 polymer entity 数据（如果需要）
        if "polymer_entity_ids" in entry_data.get("rcsb_entry_container_identifiers", {}):
            polymer_ids = entry_data["rcsb_entry_container_identifiers"]["polymer_entity_ids"]
            if polymer_ids:
                # 请求第一个 polymer entity 的详细信息
                yield from self._request_polymer_entity(polymer_ids[0])
            else:
                # 继续处理 Assembly API
                assembly_api_fields = []
                for field_name, field_def in self.field_definitions.items():
                    if "REST Assembly API" in field_def.get("api", ""):
                        assembly_api_fields.append((field_name, field_def))
                if assembly_api_fields:
                    yield from self._request_assembly_api(assembly_api_fields)
                else:
                    yield from self._save_result()
        else:
            # 继续处理 Assembly API
            assembly_api_fields = []
            for field_name, field_def in self.field_definitions.items():
                if "REST Assembly API" in field_def.get("api", ""):
                    assembly_api_fields.append((field_name, field_def))
            if assembly_api_fields:
                yield from self._request_assembly_api(assembly_api_fields)
            else:
                yield from self._save_result()

    def _request_polymer_entity(self, entity_id):
        """请求 Polymer Entity API"""
        polymer_url = f"{self.POLYMER_ENTITY_API_BASE}/{self.target_id}/{entity_id}"
        yield scrapy.Request(
            url=polymer_url,
            callback=self.parse_polymer_entity,
            dont_filter=True,
        )

    def parse_polymer_entity(self, response):
        """解析 Polymer Entity API 响应 - 提取完整的数据结构"""
        try:
            polymer_data = response.json()
        except Exception as exc:
            self.logger.warning("Polymer Entity API 响应解析失败: %s", exc)
            polymer_data = {}
        
        # 将完整的 polymer entity 数据添加到结果中
        # 这些数据会补充 GraphQL 中可能缺失的详细信息
        for key, value in polymer_data.items():
            if key not in self.result:
                self.result[key] = value
            elif isinstance(value, list) and isinstance(self.result.get(key), list):
                # 合并列表（去重）
                existing = self.result[key]
                existing_ids = {item.get("feature_id") for item in existing if isinstance(item, dict) and "feature_id" in item}
                for item in value:
                    if isinstance(item, dict) and "feature_id" in item:
                        if item["feature_id"] not in existing_ids:
                            existing.append(item)
                            existing_ids.add(item["feature_id"])
                    else:
                        existing.append(item)
            elif isinstance(value, dict) and isinstance(self.result.get(key), dict):
                # 合并字典
                self.result[key].update(value)
        
        # 继续处理 Assembly API
        assembly_api_fields = []
        for field_name, field_def in self.field_definitions.items():
            if "REST Assembly API" in field_def.get("api", ""):
                assembly_api_fields.append((field_name, field_def))
        if assembly_api_fields:
            yield from self._request_assembly_api(assembly_api_fields)
        else:
            yield from self._save_result()

    def _request_assembly_api(self, assembly_api_fields):
        """请求 Assembly API"""
        assembly_url = f"{self.ASSEMBLY_API_BASE}/{self.target_id}/1"
        yield scrapy.Request(
            url=assembly_url,
            callback=self.parse_assembly_api,
            meta={"assembly_api_fields": assembly_api_fields},
            dont_filter=True,
        )

    def parse_assembly_api(self, response):
        """解析 Assembly API 响应"""
        try:
            assembly_data = response.json()
        except Exception as exc:
            self.logger.warning("Assembly API 响应解析失败: %s", exc)
            assembly_data = {}
        
        assembly_api_fields = response.meta.get("assembly_api_fields", [])
        
        for field_name, field_def in assembly_api_fields:
            extraction_path = field_def.get("extraction_path", "")
            
            # 提取 rcsb_struct_symmetry
            if "rcsb_struct_symmetry" in extraction_path:
                if "rcsb_struct_symmetry" in assembly_data:
                    self.result["rcsb_struct_symmetry"] = assembly_data["rcsb_struct_symmetry"]
        
        # 保存结果
        self._save_result()

    def _extract_value_by_path(self, data, path):
        """根据路径提取值"""
        if not path or not data:
            return None
        
        # 清理路径（移除数组标记和条件）
        clean_path = path.split("[")[0].split("(")[0].strip()
        parts = clean_path.split(".")
        
        current = data
        for part in parts:
            if not part:
                continue
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and current:
                # 如果是列表，取第一个元素
                current = current[0].get(part) if isinstance(current[0], dict) else None
            else:
                return None
            if current is None:
                return None
        
        return current

    def _extract_full_objects_by_path(self, data, path):
        """根据路径提取完整的对象数组"""
        if not path or not data:
            return None
        
        # 清理路径
        clean_path = path.split("[")[0].split("(")[0].strip()
        parts = clean_path.split(".")
        
        current = data
        for part in parts:
            if not part:
                continue
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                # 如果是列表，返回整个列表
                return current
            else:
                return None
            if current is None:
                return None
        
        # 如果最终结果是列表，返回列表
        if isinstance(current, list):
            return current
        # 如果是单个对象，包装成列表
        elif isinstance(current, dict):
            return [current]
        return None

    def _get_key_name_from_path(self, path):
        """从路径中提取键名"""
        if not path:
            return None
        
        # 移除数组标记和条件
        clean_path = path.split("[")[0].split("(")[0].strip()
        parts = clean_path.split(".")
        
        # 返回最后一个部分作为键名
        if parts:
            return parts[-1]
        return clean_path

    def _save_result(self):
        """保存结果到文件"""
        if not self.result:
            self.logger.warning("⚠️ 没有提取到任何数据，结果为空")
            return
        
        pretty_json = json.dumps(self.result, ensure_ascii=False, indent=2)
        self.logger.info(f"\n====== 字段提取结果 (共 {len(self.result)} 个字段) ======")
        self.logger.info(f"字段列表: {', '.join(self.result.keys())}")
        self.logger.info("============================")
        
        try:
            with self.output_path.open("w", encoding="utf-8") as f:
                f.write(pretty_json)
            self.logger.info("✅ 结果已保存到: %s", self.output_path)
            self.logger.info(f"文件大小: {self.output_path.stat().st_size} bytes")
        except Exception as exc:
            self.logger.error("⚠️ 保存文件失败 (%s): %s", self.output_path, exc)
        
        # 返回结果以便 Scrapy 处理
        yield self.result
