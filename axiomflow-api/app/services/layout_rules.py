"""
布局检测规则引擎模块

对ML分类结果进行后处理：去噪、合并、验证、优化。
"""

from __future__ import annotations

import logging
from typing import Any
from dataclasses import dataclass

from .layout_detect import Region, RegionType

logger = logging.getLogger(__name__)


@dataclass
class RefinedRegion:
    """优化后的区域"""
    type: RegionType
    x0: float
    y0: float
    x1: float
    y1: float
    score: float
    source_blocks: list[dict]  # 构成此区域的原始块


class RuleEngine:
    """规则引擎：后处理、去噪、合并、验证"""

    def __init__(
        self,
        min_region_area: float = 100.0,
        min_confidence: float = 0.4,
        merge_distance_threshold: float = 20.0,
    ):
        """
        初始化规则引擎

        Args:
            min_region_area: 最小区域面积（像素²）
            min_confidence: 最小置信度阈值
            merge_distance_threshold: 合并距离阈值（像素）
        """
        self.min_region_area = min_region_area
        self.min_confidence = min_confidence
        self.merge_distance_threshold = merge_distance_threshold

    def refine_regions(
        self,
        blocks: list[dict],
        predictions: list[dict[str, Any]],
    ) -> list[RefinedRegion]:
        """
        优化区域：去噪、合并、验证

        Args:
            blocks: PDF块列表
            predictions: ML预测结果列表

        Returns:
            优化后的区域列表
        """
        if len(blocks) != len(predictions):
            logger.warning("块数量与预测数量不匹配")
            return []

        # 1. 过滤低置信度预测
        filtered_blocks = []
        for block, pred in zip(blocks, predictions):
            confidence = pred.get("confidence", 0.5)
            if confidence >= self.min_confidence:
                block["ml_type"] = pred["type"]
                block["ml_confidence"] = confidence
                filtered_blocks.append(block)

        # 2. 按类型分组
        regions_by_type = self._group_by_type(filtered_blocks)

        # 3. 对每个类型进行空间合并
        refined_regions = []
        for region_type, type_blocks in regions_by_type.items():
            merged_regions = self._merge_spatial_regions(
                type_blocks, region_type
            )
            refined_regions.extend(merged_regions)

        # 4. 验证和去噪
        refined_regions = self._validate_regions(refined_regions)

        # 5. 过滤小区域
        refined_regions = [
            r
            for r in refined_regions
            if self._calc_area(r) >= self.min_region_area
        ]

        return refined_regions

    def _group_by_type(
        self, blocks: list[dict]
    ) -> dict[RegionType, list[dict]]:
        """按预测类型分组"""
        groups: dict[RegionType, list[dict]] = {}
        
        for block in blocks:
            ml_type = block.get("ml_type")
            if not ml_type:
                continue
            
            # 确保类型是有效的RegionType
            if ml_type in ["figure", "table", "formula", "unknown"]:
                region_type: RegionType = ml_type
            elif ml_type in ["heading", "caption", "paragraph"]:
                # 这些类型通常不直接映射到RegionType
                # 可以根据需要处理或跳过
                continue
            else:
                region_type = "unknown"

            if region_type not in groups:
                groups[region_type] = []
            groups[region_type].append(block)

        return groups

    def _merge_spatial_regions(
        self, blocks: list[dict], region_type: RegionType
    ) -> list[RefinedRegion]:
        """合并空间上相邻的区域"""
        if not blocks:
            return []

        # 按位置排序
        blocks_sorted = sorted(
            blocks,
            key=lambda b: (
                float((b.get("bbox") or {}).get("y0", 0)),
                float((b.get("bbox") or {}).get("x0", 0)),
            ),
        )

        merged_regions: list[RefinedRegion] = []

        for block in blocks_sorted:
            bbox = block.get("bbox") or {}
            if not bbox:
                continue

            x0, y0, x1, y1 = (
                float(bbox.get("x0", 0)),
                float(bbox.get("y0", 0)),
                float(bbox.get("x1", 0)),
                float(bbox.get("y1", 0)),
            )
            confidence = block.get("ml_confidence", 0.5)

            # 查找是否与已有区域相邻
            merged = False
            for region in merged_regions:
                if self._should_merge(
                    (x0, y0, x1, y1),
                    (region.x0, region.y0, region.x1, region.y1),
                ):
                    # 合并区域
                    region.x0 = min(region.x0, x0)
                    region.y0 = min(region.y0, y0)
                    region.x1 = max(region.x1, x1)
                    region.y1 = max(region.y1, y1)
                    region.score = max(region.score, confidence)
                    region.source_blocks.append(block)
                    merged = True
                    break

            if not merged:
                # 创建新区域
                merged_regions.append(
                    RefinedRegion(
                        type=region_type,
                        x0=x0,
                        y0=y0,
                        x1=x1,
                        y1=y1,
                        score=confidence,
                        source_blocks=[block],
                    )
                )

        return merged_regions

    def _should_merge(
        self, bbox1: tuple[float, float, float, float], bbox2: tuple[float, float, float, float]
    ) -> bool:
        """判断两个bbox是否应该合并"""
        x1_0, y1_0, x1_1, y1_1 = bbox1
        x2_0, y2_0, x2_1, y2_1 = bbox2

        # 计算重叠
        overlap_x = max(0, min(x1_1, x2_1) - max(x1_0, x2_0))
        overlap_y = max(0, min(y1_1, y2_1) - max(y1_0, y2_0))
        overlap_area = overlap_x * overlap_y

        # 计算中心距离
        center1_x = (x1_0 + x1_1) / 2.0
        center1_y = (y1_0 + y1_1) / 2.0
        center2_x = (x2_0 + x2_1) / 2.0
        center2_y = (y2_0 + y2_1) / 2.0
        distance = ((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2) ** 0.5

        # 如果有重叠或距离很近，则合并
        if overlap_area > 0:
            return True
        if distance < self.merge_distance_threshold:
            return True

        return False

    def _validate_regions(
        self, regions: list[RefinedRegion]
    ) -> list[RefinedRegion]:
        """验证区域合理性"""
        validated = []

        for region in regions:
            # 验证bbox有效性
            if region.x1 <= region.x0 or region.y1 <= region.y0:
                logger.warning(f"无效的bbox: {region}")
                continue

            # 验证区域类型与内容的一致性
            if not self._validate_region_content(region):
                logger.debug(f"区域内容验证失败: {region.type}")
                continue

            validated.append(region)

        return validated

    def _validate_region_content(self, region: RefinedRegion) -> bool:
        """验证区域内容与类型是否一致"""
        if not region.source_blocks:
            return False

        # 简单验证：检查区域内的文本内容
        all_text = " ".join(
            b.get("text", "") for b in region.source_blocks if b.get("text")
        ).lower()

        if region.type == "formula":
            # 公式应该包含数学符号
            math_symbols = sum(
                1 for c in all_text if c in "+-*/=<>≤≥±×÷∑∏∫√"
            )
            if math_symbols == 0 and len(all_text) > 5:
                return False  # 可能是误判

        elif region.type == "table":
            # 表格应该包含多个分隔符或数字
            if "," not in all_text and "\t" not in all_text:
                # 没有明显的表格分隔符，检查是否有多个数字
                import re
                numbers = len(re.findall(r"\d+", all_text))
                if numbers < 3:
                    return False  # 可能是误判

        return True

    def _calc_area(self, region: RefinedRegion) -> float:
        """计算区域面积"""
        return (region.x1 - region.x0) * (region.y1 - region.y0)

    def convert_to_regions(
        self, refined_regions: list[RefinedRegion]
    ) -> list[Region]:
        """转换为Region对象"""
        return [
            Region(
                type=r.type,
                x0=r.x0,
                y0=r.y0,
                x1=r.x1,
                y1=r.y1,
                score=r.score,
            )
            for r in refined_regions
        ]

