import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import requests


GRAPHQL_ENDPOINT = "https://data.rcsb.org/graphql"
ENTRY_ENDPOINT_TEMPLATE = "https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
ASSEMBLY_ENDPOINT_TEMPLATE = "https://data.rcsb.org/rest/v1/core/assembly/{pdb_id}/1"

GRAPHQL_INTROSPECTION_QUERY = """
query IntrospectType($typeName: String!) {
  __type(name: $typeName) {
    name
    fields {
      name
      description
      type {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
              }
            }
          }
        }
      }
    }
  }
}
""".strip()


def unwrap_graphql_type(type_info: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    将GraphQL类型展开为基础类型和包装层信息（LIST / NON_NULL）。
    """
    wrappers: List[str] = []
    current = type_info
    while current:
        kind = current.get("kind")
        if kind in ("NON_NULL", "LIST"):
            wrappers.append(kind)
            current = current.get("ofType")
        else:
            break
    return current, wrappers


def is_scalar_graphql(type_info: Optional[Dict[str, Any]]) -> bool:
    if not type_info:
        return True
    return type_info.get("kind") in {"SCALAR", "ENUM"}


class GraphQLInspector:
    def __init__(self) -> None:
        self._type_cache: Dict[str, Dict[str, Any]] = {}

    def _fetch_type(self, type_name: str) -> Dict[str, Any]:
        if type_name in self._type_cache:
            return self._type_cache[type_name]

        response = requests.post(
            GRAPHQL_ENDPOINT,
            json={"query": GRAPHQL_INTROSPECTION_QUERY, "variables": {"typeName": type_name}},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        type_def = data.get("data", {}).get("__type")
        if not type_def:
            raise ValueError(f"无法在GraphQL模式中找到类型: {type_name}")
        self._type_cache[type_name] = type_def
        return type_def

    def get_field_map(self, type_name: str) -> Dict[str, Dict[str, Any]]:
        type_def = self._fetch_type(type_name)
        fields = type_def.get("fields", []) or []
        return {field["name"]: field for field in fields}

    def resolve_path(self, root_type: str, path: List[str]) -> str:
        current_type = root_type
        for segment in path:
            field_map = self.get_field_map(current_type)
            if segment not in field_map:
                raise ValueError(f"类型 {current_type} 中不存在字段 {segment}")
            type_info = field_map[segment]["type"]
            base_type, _ = unwrap_graphql_type(type_info)
            if not base_type or not base_type.get("name"):
                raise ValueError(f"字段 {segment} 在类型 {current_type} 中未解析到基础类型")
            current_type = base_type["name"]
        return current_type

    def describe_type(self, type_name: str) -> Dict[str, Any]:
        field_map = self.get_field_map(type_name)
        same_level = sorted(field_map.keys())
        child_fields: Dict[str, List[str]] = {}

        for field_name, field_def in field_map.items():
            base_type, _ = unwrap_graphql_type(field_def["type"])
            if base_type and not is_scalar_graphql(base_type) and base_type.get("name"):
                child_field_map = self.get_field_map(base_type["name"])
                child_fields[field_name] = sorted(child_field_map.keys())

        return {
            "type_name": type_name,
            "same_level_fields": same_level,
            "child_fields": child_fields,
        }


class RestInspector:
    def __init__(self) -> None:
        self.entry_cache: Dict[str, Dict[str, Any]] = {}
        self.assembly_cache: Dict[str, Dict[str, Any]] = {}

    def fetch_entry(self, pdb_id: str) -> Dict[str, Any]:
        if pdb_id not in self.entry_cache:
            url = ENTRY_ENDPOINT_TEMPLATE.format(pdb_id=pdb_id)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            self.entry_cache[pdb_id] = response.json()
        return self.entry_cache[pdb_id]

    def fetch_assembly(self, pdb_id: str) -> Dict[str, Any]:
        if pdb_id not in self.assembly_cache:
            url = ASSEMBLY_ENDPOINT_TEMPLATE.format(pdb_id=pdb_id)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            self.assembly_cache[pdb_id] = response.json()
        return self.assembly_cache[pdb_id]

    @staticmethod
    def extract_nodes(root: Any, path: List[str]) -> List[Any]:
        nodes = [root]
        for segment in path:
            next_nodes: List[Any] = []
            if segment == "[]":
                for node in nodes:
                    if isinstance(node, list):
                        next_nodes.extend(node)
            else:
                for node in nodes:
                    if isinstance(node, dict) and segment in node:
                        next_nodes.append(node[segment])
            nodes = next_nodes
        return nodes

    @staticmethod
    def describe_nodes(nodes: List[Any]) -> Tuple[List[str], Dict[str, List[str]]]:
        same_level: set[str] = set()
        child_fields: Dict[str, set[str]] = defaultdict(set)

        for node in nodes:
            if isinstance(node, dict):
                same_level.update(node.keys())
                for key, value in node.items():
                    if isinstance(value, dict):
                        child_fields[key].update(value.keys())
                    elif isinstance(value, list):
                        list_child_keys: set[str] = set()
                        for item in value:
                            if isinstance(item, dict):
                                list_child_keys.update(item.keys())
                        if list_child_keys:
                            child_fields[key].update(list_child_keys)

        same_level_list = sorted(same_level)
        child_fields_dict = {k: sorted(v) for k, v in child_fields.items()}
        return same_level_list, child_fields_dict


GRAPHQL_SAMPLE_IDS = {
    "default": ["1CBS"],
    "mutation": ["7TES", "5X2Q"],
}

ENTRY_SAMPLE_IDS = {
    "default": ["1CBS"],
    "em": ["7AHL"],
    "nmr": ["2MNR"],
}

ASSEMBLY_SAMPLE_IDS = {
    "default": ["1CBS", "7AHL"],
}


FIELD_CONFIG: List[Dict[str, Any]] = [
    {
        "local_field": "PDB_ID",
        "official_fields": ["rcsb_id", "rcsb_entry_container_identifiers.entry_id"],
        "source": "GraphQL",
        "api_endpoint": GRAPHQL_ENDPOINT,
        "graphql": {
            "root_type": "CoreEntry",
            "paths": [
                {"path": ["rcsb_entry_container_identifiers"]},
            ],
            "target_fields": ["entry_id", "assembly_ids", "struct_asym_ids"],
            "sample_ids": GRAPHQL_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "Macromolecule",
        "official_fields": [
            "polymer_entities.rcsb_polymer_entity.pdbx_description",
            "polymer_entities.rcsb_polymer_entity.formula_weight",
            "polymer_entities.entity_poly.type",
            "polymer_entities.entity_poly.pdbx_strand_id",
        ],
        "source": "GraphQL",
        "api_endpoint": GRAPHQL_ENDPOINT,
        "graphql": {
            "root_type": "CoreEntry",
            "paths": [
                {"path": ["polymer_entities"]},
                {"path": ["polymer_entities", "rcsb_polymer_entity"]},
                {"path": ["polymer_entities", "entity_poly"]},
            ],
            "target_fields": ["pdbx_description", "formula_weight", "type", "pdbx_strand_id"],
            "sample_ids": GRAPHQL_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "unique_Ligands",
        "official_fields": [
            "nonpolymer_entities.pdbx_entity_nonpoly.comp_id",
            "nonpolymer_entities.pdbx_entity_nonpoly.name",
        ],
        "source": "GraphQL",
        "api_endpoint": GRAPHQL_ENDPOINT,
        "graphql": {
            "root_type": "CoreEntry",
            "paths": [
                {"path": ["nonpolymer_entities"]},
                {"path": ["nonpolymer_entities", "pdbx_entity_nonpoly"]},
            ],
            "target_fields": ["comp_id", "name"],
            "sample_ids": GRAPHQL_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "Organism",
        "official_fields": ["polymer_entities.rcsb_entity_source_organism.ncbi_scientific_name"],
        "source": "GraphQL",
        "api_endpoint": GRAPHQL_ENDPOINT,
        "graphql": {
            "root_type": "CoreEntry",
            "paths": [
                {"path": ["polymer_entities", "rcsb_entity_source_organism"]},
            ],
            "target_fields": ["ncbi_scientific_name", "ncbi_taxonomy_id"],
            "sample_ids": GRAPHQL_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "Expression_System",
        "official_fields": ["polymer_entities.rcsb_entity_host_organism.ncbi_scientific_name"],
        "source": "GraphQL",
        "api_endpoint": GRAPHQL_ENDPOINT,
        "graphql": {
            "root_type": "CoreEntry",
            "paths": [
                {"path": ["polymer_entities", "rcsb_entity_host_organism"]},
            ],
            "target_fields": ["ncbi_scientific_name", "ncbi_taxonomy_id"],
            "sample_ids": GRAPHQL_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "Mutation",
        "official_fields": [
            "polymer_entities.rcsb_polymer_entity_feature.type",
            "polymer_entities.rcsb_polymer_entity_feature.name",
            "polymer_entities.rcsb_polymer_entity_feature.description",
        ],
        "source": "GraphQL",
        "api_endpoint": GRAPHQL_ENDPOINT,
        "graphql": {
            "root_type": "CoreEntry",
            "paths": [
                {"path": ["polymer_entities", "rcsb_polymer_entity_feature"]},
            ],
            "target_fields": ["type", "name", "description", "residue_range"],
            "sample_ids": GRAPHQL_SAMPLE_IDS["mutation"],
        },
    },
    {
        "local_field": "Title",
        "official_fields": ["struct.title"],
        "source": "REST",
        "api_endpoint": ENTRY_ENDPOINT_TEMPLATE,
        "rest": {
            "path": ["struct"],
            "target_fields": ["title"],
            "sample_ids": ENTRY_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "PDB_DOI",
        "official_fields": ["database2[].pdbx_doi"],
        "source": "REST",
        "api_endpoint": ENTRY_ENDPOINT_TEMPLATE,
        "rest": {
            "path": ["database2", "[]"],
            "target_fields": ["pdbx_database_accession", "pdbx_database_id", "pdbx_doi"],
            "sample_ids": ENTRY_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "Classification",
        "official_fields": ["struct_keywords.pdbx_keywords"],
        "source": "REST",
        "api_endpoint": ENTRY_ENDPOINT_TEMPLATE,
        "rest": {
            "path": ["struct_keywords"],
            "target_fields": ["pdbx_keywords", "text"],
            "sample_ids": ENTRY_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "Deposited",
        "official_fields": ["rcsb_accession_info.deposit_date"],
        "source": "REST",
        "api_endpoint": ENTRY_ENDPOINT_TEMPLATE,
        "rest": {
            "path": ["rcsb_accession_info"],
            "target_fields": ["deposit_date", "initial_release_date", "revision_date"],
            "sample_ids": ENTRY_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "Released",
        "official_fields": ["rcsb_accession_info.initial_release_date"],
        "source": "REST",
        "api_endpoint": ENTRY_ENDPOINT_TEMPLATE,
        "rest": {
            "path": ["rcsb_accession_info"],
            "target_fields": ["deposit_date", "initial_release_date", "revision_date"],
            "sample_ids": ENTRY_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "Deposition_Author",
        "official_fields": ["audit_author[].name"],
        "source": "REST",
        "api_endpoint": ENTRY_ENDPOINT_TEMPLATE,
        "rest": {
            "path": ["audit_author", "[]"],
            "target_fields": ["name", "pdbx_ordinal"],
            "sample_ids": ENTRY_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "PMID",
        "official_fields": ["citation[].pdbx_database_id_pub_med"],
        "source": "REST",
        "api_endpoint": ENTRY_ENDPOINT_TEMPLATE,
        "rest": {
            "path": ["citation", "[]"],
            "target_fields": [
                "pdbx_database_id_pub_med",
                "journal_abbrev",
                "title",
                "year",
            ],
            "sample_ids": ENTRY_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "Macromolecule_Content",
        "official_fields": [
            "rcsb_entry_info.molecular_weight",
            "rcsb_entry_info.deposited_atom_count",
            "rcsb_entry_info.polymer_entity_count",
        ],
        "source": "REST",
        "api_endpoint": ENTRY_ENDPOINT_TEMPLATE,
        "rest": {
            "path": ["rcsb_entry_info"],
            "target_fields": [
                "molecular_weight",
                "deposited_atom_count",
                "deposited_polymer_monomer_count",
                "deposited_modeled_polymer_monomer_count",
                "deposited_solvent_atom_count",
                "polymer_entity_count",
                "polymer_composition",
                "nonpolymer_entity_count",
                "deposited_model_count",
            ],
            "sample_ids": ENTRY_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "Experimental_Data_Snapshot",
        "official_fields": [
            "rcsb_entry_info.diffrn_resolution_high",
            "refine.ls_rfactor_rfree",
            "pdbx_vrpt_summary_diffraction.dccrfree",
            "em3d_reconstruction.resolution",
            "em_experiment.aggregation_state",
            "pdbx_nmr_ensemble.conformers_calculated_total_number",
            "pdbx_nmr_representative.selection_criteria",
        ],
        "source": "REST",
        "api_endpoint": ENTRY_ENDPOINT_TEMPLATE,
        "rest": {
            "paths": [
                ["rcsb_entry_info"],
                ["refine", "[]"],
                ["pdbx_vrpt_summary_diffraction", "[]"],
                ["em3d_reconstruction", "[]"],
                ["em_experiment"],
                ["pdbx_nmr_ensemble"],
                ["pdbx_nmr_representative"],
            ],
            "target_fields": [],
            "sample_ids": ENTRY_SAMPLE_IDS["default"] + ENTRY_SAMPLE_IDS["em"] + ENTRY_SAMPLE_IDS["nmr"],
        },
    },
    {
        "local_field": "Global_Symmetry",
        "official_fields": [
            "rcsb_struct_symmetry[].type",
            "rcsb_struct_symmetry[].symbol",
        ],
        "source": "REST",
        "api_endpoint": ASSEMBLY_ENDPOINT_TEMPLATE,
        "assembly": {
            "path": ["rcsb_struct_symmetry", "[]"],
            "target_fields": ["type", "symbol", "oligomeric_state", "stoichiometry"],
            "sample_ids": ASSEMBLY_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "Global_Stoichiometry",
        "official_fields": [
            "rcsb_struct_symmetry[].stoichiometry",
            "rcsb_struct_symmetry[].oligomeric_state",
        ],
        "source": "REST",
        "api_endpoint": ASSEMBLY_ENDPOINT_TEMPLATE,
        "assembly": {
            "path": ["rcsb_struct_symmetry", "[]"],
            "target_fields": ["type", "symbol", "oligomeric_state", "stoichiometry"],
            "sample_ids": ASSEMBLY_SAMPLE_IDS["default"],
        },
    },
    {
        "local_field": "cif_file",
        "official_fields": ["https://files.rcsb.org/download/{pdb_id}.cif"],
        "source": "Download",
        "api_endpoint": "https://files.rcsb.org/download/{pdb_id}.cif",
        "notes": "直接下载CIF结构文件；无需额外字段。",
    },
    {
        "local_field": "validation_image",
        "official_fields": ["https://files.rcsb.org/validation/view/{pdb_id}_multipercentile_validation.png"],
        "source": "Download",
        "api_endpoint": "https://files.rcsb.org/validation/view/{pdb_id}_multipercentile_validation.png",
        "notes": "可获取多分位验证图像；同级无额外字段。",
    },
]


def main() -> None:
    gql_inspector = GraphQLInspector()
    rest_inspector = RestInspector()
    summary: List[Dict[str, Any]] = []

    for config in FIELD_CONFIG:
        record: Dict[str, Any] = {
            "页面字段": config["local_field"],
            "官方字段": config.get("official_fields"),
            "API类型": config["source"],
            "api_endpoint": config["api_endpoint"],
        }

        if "graphql" in config:
            graphql_meta = config["graphql"]
            root_type = graphql_meta["root_type"]
            paths = graphql_meta.get("paths", [])
            path_details: List[Dict[str, Any]] = []
            same_level_union: set[str] = set()
            child_union: Dict[str, set[str]] = defaultdict(set)

            for path_def in paths:
                path = path_def.get("path", [])
                target_type = gql_inspector.resolve_path(root_type, path)
                type_desc = gql_inspector.describe_type(target_type)

                same_level_union.update(type_desc["same_level_fields"])
                for child_key, child_values in type_desc["child_fields"].items():
                    child_union[child_key].update(child_values)

                path_details.append(
                    {
                        "path": path,
                        "resolved_type": target_type,
                        "same_level_fields": type_desc["same_level_fields"],
                        "child_fields": type_desc["child_fields"],
                    }
                )

            record["graphql_paths"] = path_details
            record["同级字段"] = sorted(same_level_union)
            record["子级字段"] = {k: sorted(v) for k, v in child_union.items()}
            record["sample_ids"] = graphql_meta.get("sample_ids")

        elif "rest" in config:
            rest_meta = config["rest"]
            sample_ids = rest_meta.get("sample_ids", ENTRY_SAMPLE_IDS["default"])
            paths = rest_meta.get("paths")
            if not paths:
                paths = [rest_meta.get("path", [])]
            same_level_union: set[str] = set()
            child_union: Dict[str, set[str]] = defaultdict(set)
            path_details: List[Dict[str, Any]] = []

            for path in paths:
                path_same_level: set[str] = set()
                path_child: Dict[str, set[str]] = defaultdict(set)

                for pdb_id in sample_ids:
                    entry_data = rest_inspector.fetch_entry(pdb_id)
                    nodes = rest_inspector.extract_nodes(entry_data, path)
                    same_level, child_fields = rest_inspector.describe_nodes(nodes)
                    path_same_level.update(same_level)
                    for key, values in child_fields.items():
                        path_child[key].update(values)

                same_level_union.update(path_same_level)
                for key, values in path_child.items():
                    child_union[key].update(values)

                path_details.append(
                    {
                        "path": path,
                        "same_level_fields": sorted(path_same_level),
                        "child_fields": {k: sorted(v) for k, v in path_child.items()},
                    }
                )

            record["rest_paths"] = path_details
            record["同级字段"] = sorted(same_level_union)
            record["子级字段"] = {k: sorted(v) for k, v in child_union.items()}
            record["sample_ids"] = sample_ids

        elif "assembly" in config:
            assembly_meta = config["assembly"]
            sample_ids = assembly_meta.get("sample_ids", ASSEMBLY_SAMPLE_IDS["default"])
            path = assembly_meta.get("path", [])
            same_level_union: set[str] = set()
            child_union: Dict[str, set[str]] = defaultdict(set)

            for pdb_id in sample_ids:
                assembly_data = rest_inspector.fetch_assembly(pdb_id)
                nodes = rest_inspector.extract_nodes(assembly_data, path)
                same_level, child_fields = rest_inspector.describe_nodes(nodes)
                same_level_union.update(same_level)
                for key, values in child_fields.items():
                    child_union[key].update(values)

            record["assembly_path"] = path
            record["同级字段"] = sorted(same_level_union)
            record["子级字段"] = {k: sorted(v) for k, v in child_union.items()}
            record["sample_ids"] = sample_ids

        else:
            record["同级字段"] = []
            record["子级字段"] = {}

        if "notes" in config:
            record["notes"] = config["notes"]

        summary.append(record)

    output_path = os.path.join(os.path.dirname(__file__), "huizong.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

