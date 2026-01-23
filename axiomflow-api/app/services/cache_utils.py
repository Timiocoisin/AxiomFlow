"""
缓存工具函数

提供参数规范化、缓存键生成等功能，支持参数化缓存系统。
"""

from __future__ import annotations

import json
from typing import Any


def normalize_params_recursively(obj: Any) -> Any:
    """
    递归规范化参数（字典排序），确保参数顺序不影响缓存键。
    
    类似开源项目的 `_sort_dict_recursively` 功能。
    
    Args:
        obj: 待规范化的对象（字典、列表或其他）
    
    Returns:
        规范化后的对象
    """
    if isinstance(obj, dict):
        # 对字典按键排序，并递归处理值
        return {
            k: normalize_params_recursively(v)
            for k in sorted(obj.keys())
            for v in [obj[k]]
        }
    elif isinstance(obj, list):
        # 对列表中的每个元素递归处理
        return [normalize_params_recursively(item) for item in obj]
    else:
        # 基本类型（str, int, float, bool, None）直接返回
        return obj


def serialize_params(params: dict[str, Any]) -> str:
    """
    序列化参数为 JSON 字符串（用于存储）。
    
    Args:
        params: 参数字典
    
    Returns:
        JSON 字符串（已规范化）
    """
    normalized = normalize_params_recursively(params)
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_cache_key(
    translate_engine: str,
    translate_params: str,
    original_text: str,
) -> str:
    """
    构建缓存键（用于 InMemoryRepo 的简单字典存储）。
    
    注意：对于 MySQL，我们使用组合唯一约束，不需要这个键。
    但为了兼容 InMemoryRepo，仍然提供此方法。
    
    Args:
        translate_engine: 翻译服务名称
        translate_params: 序列化的参数字符串（JSON）
        original_text: 原文
    
    Returns:
        缓存键字符串
    """
    # 使用简单的分隔符组合（避免冲突）
    return f"{translate_engine}|||{translate_params}|||{original_text}"

