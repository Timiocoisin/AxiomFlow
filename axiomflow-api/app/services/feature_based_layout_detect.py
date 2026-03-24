"""
基于特征工程的布局检测器

整合特征提取、ML分类和规则引擎，实现与开源项目不同的布局检测方案。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from .layout_features import FeatureExtractor
from .layout_classifier import LayoutClassifier
from .layout_rules import RuleEngine, RefinedRegion
from .layout_detect import Region, RegionType
from ..core.config import settings

logger = logging.getLogger(__name__)


class FeatureBasedLayoutDetector:
    """
    基于特征工程的布局检测器（仅使用规则模式）

    使用PDF结构特征 + 规则引擎进行布局检测。
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        use_ml: bool = False,
        min_confidence: Optional[float] = None,
        min_region_area: Optional[float] = None,
        merge_distance_threshold: Optional[float] = None,
    ):
        """
        初始化布局检测器

        Args:
            model_path: 忽略（保留以兼容旧代码）
            use_ml: 忽略（始终使用规则模式）
            min_confidence: 最小置信度阈值（默认从 Settings.layout_min_confidence 读取）
            min_region_area: 最小区域面积（默认从 Settings.layout_min_region_area 读取）
            merge_distance_threshold: 合并距离阈值（默认从 Settings.layout_merge_distance_threshold 读取）
        """
        self.feature_extractor = FeatureExtractor()
        self.classifier = LayoutClassifier()

        # 如果未显式传入，则从全局配置读取，支持 .env 自定义
        if min_confidence is None:
            min_confidence = settings.layout_min_confidence
        if min_region_area is None:
            min_region_area = settings.layout_min_region_area
        if merge_distance_threshold is None:
            merge_distance_threshold = settings.layout_merge_distance_threshold

        self.rule_engine = RuleEngine(
            min_region_area=min_region_area,
            min_confidence=min_confidence,
            merge_distance_threshold=merge_distance_threshold,
        )

    def detect_regions(
        self,
        blocks: list[dict],
        page_width: float,
        page_height: float,
    ) -> list[Region]:
        """
        检测页面布局区域

        Args:
            blocks: PDF块列表（来自PyMuPDF解析）
            page_width: 页面宽度
            page_height: 页面高度

        Returns:
            检测到的区域列表
        """
        if not blocks:
            return []

        logger.debug(
            f"开始布局检测，页面大小: {page_width}x{page_height}, "
            f"块数量: {len(blocks)}"
        )

        # 1. 特征提取
        features = self._extract_features(
            blocks, page_width, page_height
        )

        # 2. 使用规则分类
        predictions = self.classifier.predict(features, return_proba=True)

        # 3. 规则引擎后处理
        refined_regions = self.rule_engine.refine_regions(
            blocks, predictions
        )

        # 4. 转换为Region对象
        regions = self.rule_engine.convert_to_regions(refined_regions)

        logger.debug(f"布局检测完成，检测到 {len(regions)} 个区域")

        return regions

    def _extract_features(
        self,
        blocks: list[dict],
        page_width: float,
        page_height: float,
    ) -> list[dict[str, Any]]:
        """提取所有块的特征"""
        features = []

        for block in blocks:
            feat = self.feature_extractor.extract_block_features(
                block, page_width, page_height, blocks
            )
            features.append(feat)

        return features



def detect_regions_feature_based(
    blocks: list[dict],
    page_width: float,
    page_height: float,
    model_path: Optional[Path] = None,
    use_ml: bool = False,
    min_confidence: Optional[float] = None,
) -> list[Region]:
    """
    便捷函数：使用基于特征的布局检测（仅使用规则模式）

    Args:
        blocks: PDF块列表
        page_width: 页面宽度
        page_height: 页面高度
        model_path: 忽略（保留以兼容旧代码）
        use_ml: 忽略（始终使用规则模式）
        min_confidence: 最小置信度阈值（默认从 Settings.layout_min_confidence 读取）

    Returns:
        检测到的区域列表
    """
    # 如果未显式传入，则从全局配置读取（支持 .env 配置）
    if min_confidence is None:
        min_confidence = settings.layout_min_confidence

    detector = FeatureBasedLayoutDetector(
        model_path=model_path,
        use_ml=False,  # 始终使用规则模式
        min_confidence=min_confidence,
    )
    return detector.detect_regions(blocks, page_width, page_height)

