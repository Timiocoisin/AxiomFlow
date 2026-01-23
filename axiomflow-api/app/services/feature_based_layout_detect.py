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

logger = logging.getLogger(__name__)


class FeatureBasedLayoutDetector:
    """
    基于特征工程的布局检测器

    与开源项目的差异：
    - 开源：纯视觉检测（YOLO ONNX模型）
    - 我们：PDF结构 + 特征工程 + 轻量ML分类器

    优势：
    - 充分利用PDF原生信息（文本块、字体、位置等）
    - CPU性能优秀（传统ML比深度学习快）
    - 可解释性强（特征重要性分析）
    - 无需深度学习依赖（仅需scikit-learn）
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        use_ml: bool = True,
        min_confidence: float = 0.4,
    ):
        """
        初始化布局检测器

        Args:
            model_path: 预训练模型路径（可选）
            use_ml: 是否使用ML分类器（如果为False，则使用纯规则）
            min_confidence: 最小置信度阈值
        """
        self.feature_extractor = FeatureExtractor()
        self.classifier = LayoutClassifier(model_path=model_path)
        self.rule_engine = RuleEngine(min_confidence=min_confidence)
        self.use_ml = use_ml and self.classifier.use_ml

        if self.use_ml and not self.classifier.is_trained:
            logger.warning(
                "ML模型未训练，将使用规则回退模式。"
                "建议先训练模型或提供预训练模型路径。"
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

        # 2. ML分类（或规则分类）
        if self.use_ml and self.classifier.is_trained:
            predictions = self.classifier.predict(
                features, return_proba=True
            )
        else:
            # 使用规则回退
            predictions = self.classifier._rule_based_predict(features)

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

    def train_model(
        self,
        training_data: list[dict[str, Any]],
        output_path: Optional[Path] = None,
    ) -> dict[str, Any]:
        """
        训练布局分类模型

        Args:
            training_data: 训练数据列表，每个元素包含：
                - 'blocks': PDF块列表
                - 'labels': 标签列表（与blocks对应）
                - 'page_width': 页面宽度
                - 'page_height': 页面高度
            output_path: 模型保存路径（可选）

        Returns:
            训练信息
        """
        if not self.use_ml:
            return {"error": "ML模式未启用"}

        all_features = []
        all_labels = []

        for data in training_data:
            blocks = data.get("blocks", [])
            labels = data.get("labels", [])
            page_width = data.get("page_width", 800.0)
            page_height = data.get("page_height", 1000.0)

            if len(blocks) != len(labels):
                logger.warning(
                    f"块数量 ({len(blocks)}) 与标签数量 ({len(labels)}) 不匹配"
                )
                continue

            features = self._extract_features(
                blocks, page_width, page_height
            )
            all_features.extend(features)
            all_labels.extend(labels)

        if not all_features:
            return {"error": "训练数据为空"}

        # 训练模型
        train_info = self.classifier.train(all_features, all_labels)

        # 保存模型
        if output_path:
            self.classifier.save_model(output_path)

        return train_info

    def get_feature_importance(self) -> dict[str, float]:
        """获取特征重要性（如果模型已训练）"""
        if not self.use_ml:
            return {}
        return self.classifier.get_feature_importance()


def detect_regions_feature_based(
    blocks: list[dict],
    page_width: float,
    page_height: float,
    model_path: Optional[Path] = None,
    use_ml: bool = True,
    min_confidence: float = 0.4,
) -> list[Region]:
    """
    便捷函数：使用基于特征的布局检测

    Args:
        blocks: PDF块列表
        page_width: 页面宽度
        page_height: 页面高度
        model_path: 预训练模型路径（可选）
        use_ml: 是否使用ML分类器
        min_confidence: 最小置信度阈值

    Returns:
        检测到的区域列表
    """
    detector = FeatureBasedLayoutDetector(
        model_path=model_path,
        use_ml=use_ml,
        min_confidence=min_confidence,
    )
    return detector.detect_regions(blocks, page_width, page_height)

