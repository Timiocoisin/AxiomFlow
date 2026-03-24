"""
布局检测规则分类器模块

使用基于规则的启发式方法进行布局分类，不使用机器学习模型。
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class LayoutClassifier:
    """
    布局分类器：基于规则的启发式方法

    支持以下类别：
    - paragraph: 普通段落
    - heading: 标题
    - caption: 图表标题
    - formula: 公式
    - figure: 图片
    - table: 表格
    """

    def __init__(self, model_path=None, **kwargs):
        """
        初始化分类器（兼容接口，但不使用模型）

        Args:
            model_path: 忽略（保留以兼容旧代码）
            **kwargs: 忽略（保留以兼容旧代码）
        """
        pass

    def predict(
        self, features: list[dict[str, Any]], return_proba: bool = False
    ) -> list[dict[str, Any]]:
        """
        预测布局类型（使用规则方法）

        Args:
            features: 特征列表
            return_proba: 是否返回概率（始终返回）

        Returns:
            预测结果列表，每个元素包含 'type' 和 'confidence'
        """
        return self._rule_based_predict(features)

    def _rule_based_predict(
        self, features: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        基于规则的分类

        使用启发式规则进行布局类型预测。
        """
        predictions = []

        for feat in features:
            # 基于特征的启发式规则
            if feat.get("starts_with_caption", 0) == 1:
                predictions.append({"type": "caption", "confidence": 0.7})
            elif feat.get("is_math_font", 0) == 1 and feat.get("math_symbol_density", 0) > 0.1:
                predictions.append({"type": "formula", "confidence": 0.7})
            elif feat.get("font_size_hierarchy", 0) > 0.7 and feat.get("is_short_line", 0) == 1:
                predictions.append({"type": "heading", "confidence": 0.6})
            elif feat.get("aspect_ratio", 1.0) > 2.0 or feat.get("aspect_ratio", 1.0) < 0.5:
                # 宽高比异常，可能是表格或图片
                if feat.get("has_numbers", 0) == 1:
                    predictions.append({"type": "table", "confidence": 0.5})
                else:
                    predictions.append({"type": "figure", "confidence": 0.5})
            else:
                predictions.append({"type": "paragraph", "confidence": 0.5})

        return predictions

