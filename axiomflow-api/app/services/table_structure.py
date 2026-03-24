"""
表格结构提取模块

从字符级解析结果中提取表格的行列结构（cells），支持不规则表格。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TableCell:
    """表格单元格"""
    row: int
    col: int
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    rowspan: int = 1
    colspan: int = 1


@dataclass
class TableStructure:
    """表格结构"""
    rows: int
    cols: int
    cells: list[TableCell]
    # 列边界（用于对齐检测）
    column_boundaries: list[float] | None = None
    # 行边界
    row_boundaries: list[float] | None = None


def extract_table_structure(
    char_blocks: list[dict[str, Any]],
    region_x0: float,
    region_y0: float,
    region_x1: float,
    region_y1: float,
) -> TableStructure | None:
    """
    从字符块列表提取表格结构
    
    Args:
        char_blocks: 字符块列表（来自 PDFMiner 深度解析）
            每个块包含: text, x0, y0, x1, y1, char_count
        region_x0, region_y0, region_x1, region_y1: 表格区域边界
    
    Returns:
        表格结构（如果检测失败则返回 None）
    """
    if not char_blocks:
        return None
    
    # 1. 按 y 坐标分组（行）
    rows_dict: dict[float, list[dict]] = {}
    tolerance_y = 3.0  # y 坐标容差（同一行的块）
    
    for block in char_blocks:
        y_center = (block.get("y0", 0) + block.get("y1", 0)) / 2
        # 找到最接近的行键
        matched_key = None
        for key in rows_dict.keys():
            if abs(y_center - key) <= tolerance_y:
                matched_key = key
                break
        
        if matched_key is None:
            matched_key = y_center
        
        if matched_key not in rows_dict:
            rows_dict[matched_key] = []
        rows_dict[matched_key].append(block)
    
    # 按 y 坐标排序（从上到下）
    sorted_rows = sorted(rows_dict.items(), key=lambda x: x[0], reverse=True)
    
    if len(sorted_rows) < 2:
        # 至少需要 2 行才能算表格
        logger.debug("表格行数不足，无法提取结构")
        return None
    
    # 2. 检测列边界（通过分析 x 坐标分布）
    all_x_coords: list[float] = []
    for _, blocks in sorted_rows:
        for block in blocks:
            all_x_coords.extend([block.get("x0", 0), block.get("x1", 0)])
    
    if not all_x_coords:
        return None
    
    # 使用简单的聚类方法找列边界
    column_boundaries = _detect_column_boundaries(all_x_coords, region_x0, region_x1)
    
    if len(column_boundaries) < 2:
        # 至少需要 2 列
        logger.debug("表格列数不足，无法提取结构")
        return None
    
    # 3. 将块分配到单元格
    cells: list[TableCell] = []
    row_boundaries: list[float] = []
    
    for row_idx, (y_key, blocks) in enumerate(sorted_rows):
        # 记录行边界
        row_y0 = min(b.get("y0", 0) for b in blocks)
        row_y1 = max(b.get("y1", 0) for b in blocks)
        row_boundaries.append((row_y0 + row_y1) / 2)
        
        # 按 x 坐标排序
        blocks_sorted = sorted(blocks, key=lambda b: b.get("x0", 0))
        
        # 为每个块找到对应的列
        for block in blocks_sorted:
            block_x0 = block.get("x0", 0)
            block_x1 = block.get("x1", 0)
            block_text = block.get("text", "").strip()
            
            if not block_text:
                continue
            
            # 找到块跨越的列范围
            col_start = _find_column_index(block_x0, column_boundaries)
            col_end = _find_column_index(block_x1, column_boundaries)
            
            if col_start is None or col_end is None:
                continue
            
            # 创建单元格
            cell = TableCell(
                row=row_idx,
                col=col_start,
                text=block_text,
                x0=block_x0,
                y0=block.get("y0", 0),
                x1=block_x1,
                y1=block.get("y1", 0),
                rowspan=1,
                colspan=max(1, col_end - col_start + 1),
            )
            cells.append(cell)
    
    if not cells:
        return None
    
    # 4. 检测合并单元格（通过分析相邻单元格的重叠）
    cells = _detect_merged_cells(cells, sorted_rows)
    
    # 5. 确定表格尺寸
    max_row = max(c.row for c in cells) if cells else 0
    max_col = max(c.col + c.colspan - 1 for c in cells) if cells else 0
    
    return TableStructure(
        rows=max_row + 1,
        cols=max_col + 1,
        cells=cells,
        column_boundaries=column_boundaries,
        row_boundaries=row_boundaries,
    )


def _detect_column_boundaries(
    x_coords: list[float],
    region_x0: float,
    region_x1: float,
    min_gap: float = 10.0,
) -> list[float]:
    """
    检测列边界（x 坐标聚类）
    
    使用简单的聚类方法：将 x 坐标分组，组间距离大于 min_gap 的视为不同列
    """
    if not x_coords:
        return []
    
    sorted_x = sorted(set(x_coords))
    
    boundaries: list[float] = [region_x0]
    current_cluster: list[float] = [sorted_x[0]]
    
    for x in sorted_x[1:]:
        # 如果与当前簇的距离小于阈值，加入当前簇
        if x - max(current_cluster) < min_gap:
            current_cluster.append(x)
        else:
            # 新簇开始，记录前一个簇的边界（取中值）
            cluster_center = sum(current_cluster) / len(current_cluster)
            boundaries.append(cluster_center)
            current_cluster = [x]
    
    # 添加最后一个簇的边界
    if current_cluster:
        cluster_center = sum(current_cluster) / len(current_cluster)
        boundaries.append(cluster_center)
    
    boundaries.append(region_x1)
    
    return boundaries


def _find_column_index(x: float, boundaries: list[float]) -> int | None:
    """找到 x 坐标对应的列索引"""
    if not boundaries or len(boundaries) < 2:
        return None
    
    for i in range(len(boundaries) - 1):
        if boundaries[i] <= x <= boundaries[i + 1]:
            return i
    
    # 如果超出范围，返回最接近的列
    if x < boundaries[0]:
        return 0
    if x > boundaries[-1]:
        return len(boundaries) - 2
    
    return None


def _detect_merged_cells(
    cells: list[TableCell],
    sorted_rows: list[tuple[float, list[dict]]],
) -> list[TableCell]:
    """
    检测合并单元格
    
    策略：
    1. 如果同一行的相邻单元格文本为空或很小，可能是合并单元格
    2. 如果上下行的单元格在相同列位置重叠，可能是跨行合并
    """
    # 按行列组织单元格
    cell_grid: dict[tuple[int, int], TableCell] = {}
    for cell in cells:
        for c in range(cell.col, cell.col + cell.colspan):
            cell_grid[(cell.row, c)] = cell
    
    # 检测跨行合并
    for row_idx in range(len(sorted_rows) - 1):
        current_row_cells = [c for c in cells if c.row == row_idx]
        next_row_cells = [c for c in cells if c.row == row_idx + 1]
        
        for curr_cell in current_row_cells:
            for next_cell in next_row_cells:
                # 检查是否在同一列且垂直重叠
                if (
                    curr_cell.col == next_cell.col
                    and curr_cell.colspan == next_cell.colspan
                    and curr_cell.y1 >= next_cell.y0 - 2  # 允许小误差
                ):
                    # 可能是跨行合并
                    curr_cell.rowspan += 1
                    # 更新边界
                    curr_cell.y1 = max(curr_cell.y1, next_cell.y1)
    
    return cells


def table_structure_to_dict(structure: TableStructure) -> dict[str, Any]:
    """将表格结构转换为字典（用于 JSON 序列化）"""
    return {
        "rows": structure.rows,
        "cols": structure.cols,
        "cells": [
            {
                "row": c.row,
                "col": c.col,
                "text": c.text,
                "x0": c.x0,
                "y0": c.y0,
                "x1": c.x1,
                "y1": c.y1,
                "rowspan": c.rowspan,
                "colspan": c.colspan,
            }
            for c in structure.cells
        ],
        "column_boundaries": structure.column_boundaries,
        "row_boundaries": structure.row_boundaries,
    }

