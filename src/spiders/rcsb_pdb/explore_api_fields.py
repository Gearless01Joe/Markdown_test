# -*- coding: utf-8 -*-
"""
RCSB PDB API 字段探索脚本

用于自动获取 RCSB PDB API 返回的所有字段，生成完整的、有结构的字段列表。
运行此脚本可以帮助我们了解每个 API 端点实际返回的所有字段。

API 端点来源：
- 所有 API 端点均来自 RCSB PDB 官方文档：https://data.rcsb.org/data-attributes.html
- REST API 文档：https://data.rcsb.org/redoc/index.html
- 端点格式：https://data.rcsb.org/rest/v1/core/{resource}/{id}

本脚本优先使用官方 OpenAPI 文档中的字段描述（如果可用）。
"""
import json
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional


# 字段名到中文的映射字典（用于生成说明）
FIELD_DESCRIPTIONS = {
    # 通用字段
    "id": "ID",
    "name": "名称",
    "title": "标题",
    "description": "描述",
    "type": "类型",
    "formula": "分子式",
    "formula_weight": "分子量",
    "weight": "重量",
    "count": "数量",
    "date": "日期",
    "year": "年份",
    "volume": "卷号",
    "pages": "页码",
    "journal": "期刊",
    "authors": "作者",
    "doi": "DOI",
    "abstract": "摘要",
    "keywords": "关键词",
    
    # RCSB 特定字段
    "rcsb_id": "RCSB ID",
    "rcsb_entry_id": "条目 ID",
    "rcsb_entity_id": "实体 ID",
    "entry_id": "条目 ID",
    "entity_id": "实体 ID",
    "assembly_id": "装配 ID",
    "comp_id": "组分 ID",
    "pubmed_id": "PubMed ID",
    
    # PDBx 字段
    "pdbx_description": "描述",
    "pdbx_keywords": "关键词",
    "pdbx_number_of_molecules": "分子数量",
    "pdbx_mutation": "突变标志",
    "pdbx_fragment": "片段标志",
    "pdbx_ec_number": "EC 编号",
    "pdbx_strand_id": "链 ID",
    "pdbx_formal_charge": "形式电荷",
    "pdbx_formula_weight": "分子量",
    "pdbx_database_id_DOI": "DOI",
    "pdbx_database_id_PubMed": "PubMed ID",
    
    # NCBI 字段
    "ncbi_scientific_name": "NCBI 学名",
    "ncbi_taxonomy_id": "NCBI 分类 ID",
    "ncbi_common_names": "通用名称列表",
    "ncbi_parent_scientific_name": "父级学名",
    "ncbi_parent_taxonomy_id": "父级分类 ID",
    
    # 其他
    "scientific_name": "学名",
    "common_name": "通用名称",
    "source_type": "来源类型",
    "taxonomy_lineage": "分类谱系",
    "taxonomy_lineage_path": "分类谱系路径",
    "provenance_source": "来源证明",
    "feature_positions": "特征位置",
    "beg_seq_num": "起始序列号",
    "end_seq_num": "结束序列号",
    "deposit_date": "提交日期",
    "initial_release_date": "首次发布日期",
    "revision_date": "修订日期",
    "molecular_weight": "分子量",
    "deposited_atom_count": "提交的原子数",
    "polymer_entity_count": "聚合物实体数量",
    "nonpolymer_entity_count": "非聚合物实体数量",
    "method": "实验方法",
    "resolution": "分辨率",
    "ls_dres_high": "分辨率",
    "ls_rfactor_rwork": "R-work 值",
    "ls_rfactor_rfree": "R-free 值",
    "symmetry": "对称性",
    "stoichiometry": "化学计量",
    "oligomeric_state": "寡聚状态",
    
    # 更多字段
    "audit": "审计",
    "author": "作者",
    "ordinal": "序号",
    "country": "国家",
    "temperature": "温度",
    "temp": "温度",
    "density": "密度",
    "solvent": "溶剂",
    "software": "软件",
    "version": "版本",
    "classification": "分类",
    "revision": "修订",
    "status": "状态",
    "code": "代码",
    "accession": "访问",
    "support": "支持",
    "funding": "资金",
    "grant": "资助",
    "organization": "组织",
    "detector": "检测器",
    "radiation": "辐射",
    "source": "来源",
    "wavelength": "波长",
    "protocol": "协议",
    "scattering": "散射",
    "monochromatic": "单色",
    "synchrotron": "同步辐射",
    "beamline": "光束线",
    "site": "站点",
    "crystal": "晶体",
    "grow": "生长",
    "ph": "pH",
    "details": "详情",
    "matthews": "Matthews",
    "sol": "溶剂",
    "percent": "百分比",
    "number": "数量",
    "measured": "测量",
    "unique": "唯一",
    "possible": "可能",
    "rmerge": "Rmerge",
    "rrim": "RRim",
    "cchalf": "CC1/2",
    "iover_sigma": "I/σ",
    "net": "净",
    "shell": "壳层",
    "cycle": "循环",
    "atoms": "原子",
    "total": "总计",
    "ligand": "配体",
    "nucleic_acid": "核酸",
    "protein": "蛋白质",
    "restr": "约束",
    "dev_ideal": "理想偏差",
    "overall": "总体",
    "suml": "总和",
    "cross_valid": "交叉验证",
    "sigma": "σ",
    "phase_error": "相位误差",
    "shrinkage": "收缩",
    "radii": "半径",
    "vdw": "范德华",
    "probe": "探针",
    "stereochemistry": "立体化学",
    "target": "目标",
    "values": "值",
    "model": "模型",
    "combined": "组合",
    "selected": "选择",
    "maximum": "最大值",
    "minimum": "最小值",
    "priority": "优先级",
    "determination": "确定",
    "methodology": "方法学",
    "programs": "程序",
    "taxonomy": "分类学",
    "hybrid": "混合",
    "molecular": "分子",
    "monomer": "单体",
    "initial": "初始",
    "deposition": "提交",
    "received": "接收",
    "format": "格式",
    "compatible": "兼容",
    "process": "处理",
    "content": "内容",
    "provider": "提供者",
    "major": "主要",
    "minor": "次要",
    "group": "组",
    "deposit": "提交",
    "vrpt": "验证报告",
    "summary": "摘要",
    "diffraction": "衍射",
    "geometry": "几何",
    "attempted": "尝试",
    "steps": "步骤",
    "report": "报告",
    "creation": "创建",
    "dcc_r": "DCC R",
    "eds_r": "EDS R",
    "fo_fc_correlation": "Fo-Fc 相关性",
    "padilla_yeates": "Padilla-Yeates",
    "l2_mean": "L2 均值",
    "lmean": "L 均值",
    "wilson": "Wilson",
    "baniso": "各向异性 B",
    "bestimate": "B 估计",
    "acentric": "非中心",
    "centric": "中心",
    "outliers": "异常值",
    "bulk": "整体",
    "k": "K",
    "anisotropy": "各向异性",
    "completeness": "完整性",
    "fitness": "拟合度",
    "miller": "Miller",
    "indices": "指数",
    "reflns": "反射",
    "free": "自由",
    "obs": "观测",
    "percent_free": "自由百分比",
    "trans_ncs": "平移 NCS",
    "bfactor": "B 因子",
    "ccp4": "CCP4",
    "dccrfree": "DCC Rfree",
    "edsres": "EDS 分辨率",
    "high": "高",
    "low": "低",
    "iover_sigma": "I/σ",
    "angles_rmsz": "角度 RMSZ",
    "bonds_rmsz": "键 RMSZ",
    "clashscore": "碰撞评分",
    "num_hreduce": "氢还原数",
    "num_angles": "角度数",
    "num_bonds": "键数",
    "percent_ramachandran": "Ramachandran 百分比",
    "percent_rotamer": "旋转异构体百分比",
    "percent_rsrz": "RSRZ 百分比",
    "percent_cbeta": "Cβ 百分比",
    "deviations": "偏差",
    "gt": "大于",
    "zpdb": "Z PDB",
}


# 全局变量：官方字段描述（在 main 函数中加载）
OFFICIAL_FIELD_DESCRIPTIONS = {}


def load_official_field_descriptions() -> Dict[str, str]:
    """加载官方字段描述"""
    try:
        official_desc_file = Path(__file__).parent / "inhance" / "official_field_descriptions.json"
        if official_desc_file.exists():
            with official_desc_file.open("r", encoding="utf-8") as f:
                descriptions = json.load(f)
            print(f"[INFO] 已加载 {len(descriptions)} 个官方字段描述")
            return descriptions
    except Exception as e:
        print(f"[WARN] 无法加载官方字段描述: {e}")
    return {}


def get_field_description(field_name: str) -> str:
    """根据字段名生成中文说明，优先使用官方文档中的描述"""
    # 1. 优先使用官方文档中的描述（最准确）
    if OFFICIAL_FIELD_DESCRIPTIONS:
        # 尝试完整字段名匹配
        if field_name in OFFICIAL_FIELD_DESCRIPTIONS:
            desc = OFFICIAL_FIELD_DESCRIPTIONS[field_name]
            return desc
        
        # 尝试简化字段名匹配（去掉前缀）
        simple_name = field_name.split(".")[-1].split("_")[-1] if "." in field_name or "_" in field_name else field_name
        if simple_name in OFFICIAL_FIELD_DESCRIPTIONS:
            desc = OFFICIAL_FIELD_DESCRIPTIONS[simple_name]
            return desc
    
    # 2. 使用本地映射字典
    if field_name in FIELD_DESCRIPTIONS:
        return FIELD_DESCRIPTIONS[field_name]
    
    field_lower = field_name.lower()
    
    # 尝试匹配完整字段名（按优先级排序）
    # 先匹配较长的关键词（更具体）
    sorted_keys = sorted(FIELD_DESCRIPTIONS.keys(), key=len, reverse=True)
    for key in sorted_keys:
        key_lower = key.lower()
        # 完全匹配
        if field_lower == key_lower:
            return FIELD_DESCRIPTIONS[key]
        # 后缀匹配（去掉前缀）
        if field_lower.endswith(f"_{key_lower}") or field_lower.endswith(f".{key_lower}"):
            return FIELD_DESCRIPTIONS[key]
        # 包含匹配（但避免太短的词）
        if len(key_lower) > 4 and key_lower in field_lower:
            # 确保是完整的词，不是部分匹配
            if f"_{key_lower}_" in f"_{field_lower}_" or field_lower.startswith(f"{key_lower}_") or field_lower.endswith(f"_{key_lower}"):
                return FIELD_DESCRIPTIONS[key]
    
    # 根据字段名推断（更详细的规则）
    if "id" in field_lower:
        if "entry" in field_lower:
            return "条目 ID"
        elif "entity" in field_lower:
            return "实体 ID"
        elif "assembly" in field_lower:
            return "装配 ID"
        elif "comp" in field_lower or "chem" in field_lower:
            return "组分 ID"
        elif "pubmed" in field_lower:
            return "PubMed ID"
        else:
            return "ID"
    elif "name" in field_lower:
        if "scientific" in field_lower:
            return "学名"
        elif "common" in field_lower:
            return "通用名称"
        else:
            return "名称"
    elif "description" in field_lower or "desc" in field_lower:
        return "描述"
    elif "weight" in field_lower or "mass" in field_lower:
        if "formula" in field_lower or "molecular" in field_lower:
            return "分子量"
        else:
            return "重量"
    elif "count" in field_lower or "number" in field_lower:
        return "数量"
    elif "date" in field_lower:
        if "deposit" in field_lower:
            return "提交日期"
        elif "release" in field_lower:
            return "发布日期"
        elif "revision" in field_lower:
            return "修订日期"
        else:
            return "日期"
    elif "type" in field_lower:
        return "类型"
    elif "formula" in field_lower:
        return "分子式"
    elif "symmetry" in field_lower:
        return "对称性"
    elif "validation" in field_lower:
        return "验证信息"
    elif "feature" in field_lower:
        return "特征信息"
    elif "annotation" in field_lower:
        return "注释信息"
    elif "organism" in field_lower:
        if "source" in field_lower:
            return "来源物种信息"
        elif "host" in field_lower:
            return "宿主物种信息"
        else:
            return "物种信息"
    elif "host" in field_lower:
        return "宿主信息"
    elif "mutation" in field_lower:
        return "突变信息"
    elif "lineage" in field_lower:
        return "分类谱系"
    elif "position" in field_lower:
        return "位置信息"
    elif "author" in field_lower:
        return "作者信息"
    elif "citation" in field_lower:
        return "引用信息"
    elif "journal" in field_lower:
        return "期刊信息"
    elif "cell" in field_lower:
        if "length" in field_lower:
            return "晶胞长度"
        else:
            return "晶胞信息"
    elif field_lower == "length_a" or field_lower.endswith("_length_a"):
        return "a 轴长度"
    elif field_lower == "length_b" or field_lower.endswith("_length_b"):
        return "b 轴长度"
    elif field_lower == "length_c" or field_lower.endswith("_length_c"):
        return "c 轴长度"
    elif "length" in field_lower:
        return "长度"
    elif "angle" in field_lower:
        if "alpha" in field_lower:
            return "α 角度"
        elif "beta" in field_lower:
            return "β 角度"
        elif "gamma" in field_lower:
            return "γ 角度"
        else:
            return "角度"
    elif "method" in field_lower:
        return "实验方法"
    elif "resolution" in field_lower or "res" in field_lower:
        return "分辨率"
    elif "r_factor" in field_lower or "rfactor" in field_lower:
        return "R 因子"
    elif "refine" in field_lower:
        return "精修信息"
    elif "crystal" in field_lower:
        return "晶体信息"
    elif "diffrn" in field_lower or "diffraction" in field_lower:
        return "衍射信息"
    elif "audit" in field_lower:
        return "审计信息"
    elif "revision" in field_lower:
        return "修订信息"
    elif "status" in field_lower:
        return "状态信息"
    elif "keyword" in field_lower:
        return "关键词"
    elif "accession" in field_lower:
        return "访问信息"
    elif "container" in field_lower and "identifier" in field_lower:
        return "容器标识符"
    elif "stoichiometry" in field_lower:
        return "化学计量"
    elif "oligomeric" in field_lower:
        return "寡聚状态"
    else:
        # 尝试从字段名中提取有意义的部分
        parts = field_name.split("_")
        if len(parts) > 1:
            # 尝试匹配各个部分
            for part in reversed(parts):  # 从后往前，优先匹配后面的部分
                if part in FIELD_DESCRIPTIONS:
                    return FIELD_DESCRIPTIONS[part]
                part_lower = part.lower()
                for key, desc in FIELD_DESCRIPTIONS.items():
                    if part_lower == key.lower():
                        return desc
        
        # 如果还是找不到，尝试根据常见模式推断
        if field_lower.startswith("pdbx_"):
            # PDBx 扩展字段，去掉前缀后重试
            without_prefix = field_lower[5:]  # 去掉 "pdbx_"
            return get_field_description(without_prefix) if without_prefix != field_lower else "PDBx 扩展字段"
        elif field_lower.startswith("rcsb_"):
            # RCSB 扩展字段，去掉前缀后重试
            without_prefix = field_lower[5:]  # 去掉 "rcsb_"
            return get_field_description(without_prefix) if without_prefix != field_lower else "RCSB 扩展字段"
        
        return "字段"


def build_field_structure(data: Any, prefix: str = "", level: int = 0) -> List[Dict[str, Any]]:
    """递归构建字段结构（保持层级关系）"""
    fields = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            field_info = {
                "field": key,
                "full_path": full_key,
                "level": level,
                "description": get_field_description(key),
                "type": type(value).__name__
            }
            
            # 如果是字典或列表，递归处理
            if isinstance(value, dict) and len(value) > 0:
                field_info["is_object"] = True
                field_info["children"] = build_field_structure(value, full_key, level + 1)
                fields.append(field_info)
            elif isinstance(value, list) and len(value) > 0:
                field_info["is_array"] = True
                # 处理列表中的第一个元素
                if isinstance(value[0], dict):
                    field_info["children"] = build_field_structure(value[0], full_key, level + 1)
                fields.append(field_info)
            else:
                field_info["is_leaf"] = True
                fields.append(field_info)
    
    return fields


def format_fields_markdown(fields: List[Dict[str, Any]], indent: int = 0) -> str:
    """将字段结构格式化为 Markdown 格式（类似文档格式）"""
    lines = []
    indent_str = "  " * indent
    
    for field in fields:
        field_name = field["field"]
        description = field["description"]
        field_type = field["type"]
        
        # 构建字段行（类似文档格式：- `field_name` - 描述）
        line = f"{indent_str}- `{field_name}` - {description}"
        lines.append(line)
        
        # 递归处理子字段
        if field.get("children"):
            child_lines = format_fields_markdown(field["children"], indent + 1)
            lines.append(child_lines)
    
    return "\n".join(lines)


def explore_nonpolymer_entity_api(entry_id: str, entity_id: Optional[str] = None) -> Dict[str, Any]:
    """探索 Non-polymer Entity API 的所有字段"""
    # 如果没有提供 entity_id，先从 Entry API 获取
    if entity_id is None:
        entry_url = f"https://data.rcsb.org/rest/v1/core/entry/{entry_id}"
        try:
            entry_response = requests.get(entry_url, timeout=10)
            entry_response.raise_for_status()
            entry_data = entry_response.json()
            container_ids = entry_data.get("rcsb_entry_container_identifiers", {})
            nonpolymer_ids = container_ids.get("nonpolymer_entity_ids", [])
            if nonpolymer_ids:
                entity_id = nonpolymer_ids[0]
            else:
                return {
                    "api_name": "Non-polymer Entity",
                    "api_endpoint": f"https://data.rcsb.org/rest/v1/core/nonpolymer_entity/{entry_id}/?",
                    "status": "error",
                    "error": f"Entry {entry_id} 没有 nonpolymer entities"
                }
        except Exception as e:
            return {
                "api_name": "Non-polymer Entity",
                "api_endpoint": f"https://data.rcsb.org/rest/v1/core/nonpolymer_entity/{entry_id}/?",
                "status": "error",
                "error": f"无法获取 nonpolymer entity IDs: {str(e)}"
            }
    
    url = f"https://data.rcsb.org/rest/v1/core/nonpolymer_entity/{entry_id}/{entity_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 构建字段结构
        fields_structure = build_field_structure(data)
        
        # 获取所有字段路径（扁平化）
        all_fields_flat = []
        def collect_fields(fields_list, parent=""):
            for field in fields_list:
                full_path = f"{parent}.{field['field']}" if parent else field['field']
                all_fields_flat.append(full_path)
                if field.get("children"):
                    collect_fields(field["children"], full_path)
        
        collect_fields(fields_structure)
        
        return {
            "api_name": "Non-polymer Entity",
            "api_endpoint": url,
            "status": "success",
            "total_fields": len(all_fields_flat),
            "fields_structure": fields_structure,
            "all_fields_flat": sorted(all_fields_flat),
            "markdown_format": format_fields_markdown(fields_structure)
        }
    except requests.exceptions.RequestException as e:
        return {
            "api_name": "Non-polymer Entity",
            "api_endpoint": url,
            "status": "error",
            "error": str(e)
        }
    except Exception as e:
        return {
            "api_name": "Non-polymer Entity",
            "api_endpoint": url,
            "status": "error",
            "error": str(e)
        }


def explore_api(api_name: str, url: str) -> Dict[str, Any]:
    """探索指定 API 的所有字段"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 构建字段结构
        fields_structure = build_field_structure(data)
        
        # 获取所有字段路径（扁平化）
        all_fields_flat = []
        def collect_fields(fields_list, parent=""):
            for field in fields_list:
                full_path = f"{parent}.{field['field']}" if parent else field['field']
                all_fields_flat.append(full_path)
                if field.get("children"):
                    collect_fields(field["children"], full_path)
        
        collect_fields(fields_structure)
        
        return {
            "api_name": api_name,
            "api_endpoint": url,
            "status": "success",
            "total_fields": len(all_fields_flat),
            "fields_structure": fields_structure,
            "all_fields_flat": sorted(all_fields_flat),
            "markdown_format": format_fields_markdown(fields_structure)
        }
    except requests.exceptions.RequestException as e:
        return {
            "api_name": api_name,
            "api_endpoint": url,
            "status": "error",
            "error": str(e)
        }
    except Exception as e:
        return {
            "api_name": api_name,
            "api_endpoint": url,
            "status": "error",
            "error": str(e)
        }


def get_entry_info(entry_id: str) -> Dict[str, Any]:
    """获取 Entry 信息，用于提取 entity_ids"""
    url = f"https://data.rcsb.org/rest/v1/core/entry/{entry_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def find_pdb_with_data(api_type: str, pdb_ids: List[str]) -> tuple:
    """从多个 PDB ID 中找到有数据的那个
    
    Returns:
        (entry_id, entity_id, data) 或 (None, None, None)
    """
    for entry_id in pdb_ids:
        entry_data = get_entry_info(entry_id)
        if "error" in entry_data:
            continue
        
        container_ids = entry_data.get("rcsb_entry_container_identifiers", {})
        
        if api_type == "Polymer Entity":
            polymer_ids = container_ids.get("polymer_entity_ids", [])
            if polymer_ids:
                return (entry_id, polymer_ids[0], entry_data)
        
        elif api_type == "Non-polymer Entity":
            nonpolymer_ids = container_ids.get("nonpolymer_entity_ids", [])
            if nonpolymer_ids:
                return (entry_id, nonpolymer_ids[0], entry_data)
        
        elif api_type == "Assembly":
            # Assembly 通常都有，至少 assembly_id=1
            return (entry_id, "1", entry_data)
        
        elif api_type == "Entry":
            return (entry_id, None, entry_data)
    
    return (None, None, None)


def main():
    """主函数：探索所有 API 端点"""
    global OFFICIAL_FIELD_DESCRIPTIONS
    
    print("=" * 80)
    print("RCSB PDB API 字段探索工具")
    print("=" * 80)
    print()
    
    # 加载官方字段描述
    OFFICIAL_FIELD_DESCRIPTIONS = load_official_field_descriptions()
    print()
    
    # 定义多个备选 PDB ID（确保能获取到各种类型的数据）
    # 这些 PDB ID 来自 RCSB PDB 官方数据库，选择不同类型的结构
    pdb_ids = [
        "7IAQ",  # 有 polymer entity，可能有 nonpolymer entity
        "1A2B",  # 经典结构，通常有完整数据
        "4HHB",  # 血红蛋白，有多个 entities
        "1CRN",  # 小蛋白，结构简单
        "7NH1",  # 较新的结构，可能有完整数据
    ]
    
    print(f"使用备选 PDB ID: {', '.join(pdb_ids)}")
    print("如果某个 ID 缺少数据，将自动切换到下一个\n")
    
    # 定义要探索的 API（不指定具体 entry_id，由函数动态选择）
    apis_to_explore = [
        ("Entry", None),  # 使用第一个可用的 PDB ID
        ("Polymer Entity", None),  # 动态查找有 polymer entity 的 PDB ID
        ("Non-polymer Entity", None),  # 动态查找有 nonpolymer entity 的 PDB ID
        ("Assembly", None),  # 使用第一个可用的 PDB ID
        ("Chemical Component", "HEM"),  # 化学组分不依赖 PDB ID
    ]
    
    results = {}
    markdown_output = []
    
    # 先获取第一个可用的 Entry 数据，用于后续查找
    entry_id_used = None
    entry_data_cache = None
    
    for api_name, url_or_param in apis_to_explore:
        print(f"探索 {api_name} API...")
        
        if api_name == "Entry":
            # Entry API：使用第一个可用的 PDB ID
            entry_id, _, entry_data = find_pdb_with_data("Entry", pdb_ids)
            if entry_id:
                entry_id_used = entry_id
                entry_data_cache = entry_data
                url = f"https://data.rcsb.org/rest/v1/core/entry/{entry_id}"
                result = explore_api(api_name, url)
                print(f"  使用 PDB ID: {entry_id}")
            else:
                result = {
                    "api_name": api_name,
                    "api_endpoint": "N/A",
                    "status": "error",
                    "error": "所有 PDB ID 都无法获取 Entry 数据"
                }
        
        elif api_name == "Polymer Entity":
            # Polymer Entity API：查找有 polymer entity 的 PDB ID
            entry_id, entity_id, entry_data = find_pdb_with_data("Polymer Entity", pdb_ids)
            if entry_id and entity_id:
                url = f"https://data.rcsb.org/rest/v1/core/polymer_entity/{entry_id}/{entity_id}"
                result = explore_api(api_name, url)
                print(f"  使用 PDB ID: {entry_id}, Entity ID: {entity_id}")
            else:
                result = {
                    "api_name": api_name,
                    "api_endpoint": "N/A",
                    "status": "error",
                    "error": "所有 PDB ID 都没有 polymer entities"
                }
        
        elif api_name == "Non-polymer Entity":
            # Non-polymer Entity API：查找有 nonpolymer entity 的 PDB ID
            entry_id, entity_id, entry_data = find_pdb_with_data("Non-polymer Entity", pdb_ids)
            if entry_id and entity_id:
                result = explore_nonpolymer_entity_api(entry_id, entity_id)
                print(f"  使用 PDB ID: {entry_id}, Entity ID: {entity_id}")
            else:
                result = {
                    "api_name": api_name,
                    "api_endpoint": "N/A",
                    "status": "error",
                    "error": "所有 PDB ID 都没有 nonpolymer entities"
                }
        
        elif api_name == "Assembly":
            # Assembly API：使用第一个可用的 PDB ID
            entry_id, assembly_id, entry_data = find_pdb_with_data("Assembly", pdb_ids)
            if entry_id:
                url = f"https://data.rcsb.org/rest/v1/core/assembly/{entry_id}/{assembly_id}"
                result = explore_api(api_name, url)
                print(f"  使用 PDB ID: {entry_id}, Assembly ID: {assembly_id}")
            else:
                result = {
                    "api_name": api_name,
                    "api_endpoint": "N/A",
                    "status": "error",
                    "error": "所有 PDB ID 都无法获取 Assembly 数据"
                }
        
        elif api_name == "Chemical Component":
            # Chemical Component API：使用指定的 comp_id
            comp_id = url_or_param if url_or_param else "HEM"
            url = f"https://data.rcsb.org/rest/v1/core/chemcomp/{comp_id}"
            result = explore_api(api_name, url)
            print(f"  使用 Comp ID: {comp_id}")
        
        else:
            # 其他 API：直接使用 URL
            if url_or_param:
                result = explore_api(api_name, url_or_param)
            else:
                result = {
                    "api_name": api_name,
                    "api_endpoint": "N/A",
                    "status": "error",
                    "error": "未指定 URL 或参数"
                }
        
        results[api_name.lower().replace(" ", "_")] = result
        
        if result["status"] == "success":
            print(f"  [OK] 找到 {result['total_fields']} 个字段")
            markdown_output.append(f"## {api_name} Attributes")
            markdown_output.append(f"\n**API 端点**: `{result['api_endpoint']}`\n")
            markdown_output.append("### 所有字段列表\n")
            markdown_output.append(result["markdown_format"])
            markdown_output.append("\n---\n")
        else:
            print(f"  [ERROR] 错误: {result.get('error', 'Unknown error')}")
            markdown_output.append(f"## {api_name} Attributes")
            api_endpoint = result.get('api_endpoint', url if url else 'N/A')
            markdown_output.append(f"\n**API 端点**: `{api_endpoint}`\n")
            markdown_output.append(f"**错误**: {result.get('error', 'Unknown error')}\n")
            markdown_output.append("\n---\n")
    
    # 保存 JSON 结果
    output_dir = Path(__file__).parent / "inhance"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_file = output_dir / "api_fields_exploration.json"
    with json_file.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] JSON 结果已保存到: {json_file}")
    
    # 保存 Markdown 结果
    md_file = output_dir / "api_fields_complete.md"
    with md_file.open("w", encoding="utf-8") as f:
        f.write("# RCSB PDB API 完整字段列表\n\n")
        f.write("> 本文档由 `explore_api_fields.py` 自动生成\n\n")
        f.write("---\n\n")
        f.write("\n".join(markdown_output))
    print(f"[OK] Markdown 结果已保存到: {md_file}")
    
    print("\n" + "=" * 80)
    print("完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
