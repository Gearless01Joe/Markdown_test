# -*- coding: utf-8 -*-
"""
字段过滤模块 - 根据配置精确控制提取哪些字段
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class FieldFilter:
    """字段过滤器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化过滤器。

        参数:
            config_path (Optional[str]): JSON 配置文件路径，None 表示不过滤。
        """
        self.config = None
        if config_path:
            self._load_config(config_path)
    
    def _load_config(self, config_path: str):
        """
        加载 JSON 配置文件。

        参数:
            config_path (str): 配置文件路径。
        """
        config_file = Path(config_path)
        if not config_file.exists():
            return
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except Exception:
            self.config = None
    
    def filter_data(self, data: Dict[str, Any], section: str) -> Dict[str, Any]:
        """
        根据配置过滤指定板块的数据。

        参数:
            data (Dict[str, Any]): 待过滤的数据。
            section (str): 配置中定义的板块名称。
        返回:
            Dict[str, Any]: 过滤后的数据。
        """
        if not self.config or section not in self.config:
            return data
        
        config = self.config[section]
        mode = self.config.get("mode", "whitelist")
        
        # 统一处理白名单和黑名单
        if mode == "whitelist":
            include_all = config.get("include_all", True)
            include_fields = config.get("include_fields", [])
            result = dict(data) if include_all else {k: data[k] for k in include_fields if k in data}
        else:
            result = dict(data)
        
        # 排除字段
        for field in config.get("exclude_fields", []):
            result.pop(field, None)
        
        # 应用字段规则
        for field_path, rule in config.get("field_rules", {}).items():
            self._apply_rule(result, field_path, rule)
        
        return result
    
    def _apply_rule(self, data: Dict[str, Any], field_path: str, rule: Dict[str, Any]):
        """
        应用字段规则到指定路径。

        参数:
            data (Dict[str, Any]): 当前数据。
            field_path (str): 点分路径。
            rule (Dict[str, Any]): include/exclude 子字段规则。
        """
        parts = field_path.split(".")
        current = data
        
        # 导航到目标字段
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                return
            current = current[part]
        
        target = parts[-1]
        if target not in current:
            return
        
        value = current[target]
        include_all = rule.get("include_all", True)
        include_subfields = rule.get("include_subfields", [])
        exclude_subfields = rule.get("exclude_subfields", [])
        
        if isinstance(value, list):
            current[target] = [
                self._filter_item(item, include_all, include_subfields, exclude_subfields)
                if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, dict):
            current[target] = self._filter_item(value, include_all, include_subfields, exclude_subfields)
    
    def _filter_item(self, item: Dict[str, Any], include_all: bool,
                    include_subfields: List[str], exclude_subfields: List[str]) -> Dict[str, Any]:
        """
        根据规则过滤字典项。

        参数:
            item (Dict[str, Any]): 原始字典。
            include_all (bool): 是否包含全部子字段。
            include_subfields (List[str]): 白名单字段。
            exclude_subfields (List[str]): 黑名单字段。
        返回:
            Dict[str, Any]: 过滤后的字典。
        """
        if include_all:
            result = {k: v for k, v in item.items() if k not in exclude_subfields}
        else:
            result = {k: item[k] for k in include_subfields if k in item}
        return result
