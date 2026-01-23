"""
布局检测轻量分类器模块

使用传统机器学习算法（Random Forest/XGBoost）进行布局分类。
"""

from __future__ import annotations

import logging
from typing import Any, Optional
import pickle
from pathlib import Path

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    # 定义dummy类以避免导入错误
    class RandomForestClassifier:
        pass
    class StandardScaler:
        pass
    np = None

logger = logging.getLogger(__name__)


class LayoutClassifier:
    """
    布局分类器：基于传统ML算法

    使用Random Forest进行多类别分类，支持以下类别：
    - paragraph: 普通段落
    - heading: 标题
    - caption: 图表标题
    - formula: 公式
    - figure: 图片
    - table: 表格
    """

    # 类别映射
    CLASS_LABELS = ["paragraph", "heading", "caption", "formula", "figure", "table"]
    CLASS_TO_IDX = {label: idx for idx, label in enumerate(CLASS_LABELS)}
    IDX_TO_CLASS = {idx: label for idx, label in enumerate(CLASS_LABELS)}

    def __init__(
        self,
        model_path: Optional[Path] = None,
        n_estimators: int = 100,
        max_depth: int = 20,
        random_state: int = 42,
    ):
        """
        初始化分类器

        Args:
            model_path: 预训练模型路径（可选）
            n_estimators: Random Forest树的数量
            max_depth: 树的最大深度
            random_state: 随机种子
        """
        if not SKLEARN_AVAILABLE:
            logger.warning(
                "scikit-learn 未安装，布局分类器将使用规则回退模式。"
            )
            self.use_ml = False
            return

        self.use_ml = True
        self.scaler = StandardScaler()
        self.classifier = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,  # 使用所有CPU核心
            class_weight="balanced",  # 处理类别不平衡
        )
        self.is_trained = False

        # 如果提供了模型路径，尝试加载
        if model_path and model_path.exists():
            self.load_model(model_path)

    def train(
        self,
        features: list[dict[str, Any]],
        labels: list[str],
    ) -> dict[str, Any]:
        """
        训练分类器

        Args:
            features: 特征列表（每个元素是一个特征字典）
            labels: 标签列表

        Returns:
            训练信息（准确率等）
        """
        if not self.use_ml:
            logger.warning("scikit-learn 未安装，无法训练模型。")
            return {"error": "scikit-learn not available"}

        if not features or not labels:
            logger.warning("训练数据为空。")
            return {"error": "empty training data"}

        # 转换为numpy数组
        X = self._features_to_array(features)
        y = [self.CLASS_TO_IDX.get(label, 0) for label in labels]

        # 标准化特征
        X_scaled = self.scaler.fit_transform(X)

        # 训练
        self.classifier.fit(X_scaled, y)

        self.is_trained = True

        # 计算训练准确率
        train_score = self.classifier.score(X_scaled, y)

        logger.info(f"模型训练完成，训练准确率: {train_score:.4f}")

        return {
            "train_accuracy": train_score,
            "n_samples": len(features),
            "n_features": X.shape[1],
        }

    def predict(
        self, features: list[dict[str, Any]], return_proba: bool = False
    ) -> list[dict[str, Any]]:
        """
        预测布局类型

        Args:
            features: 特征列表
            return_proba: 是否返回概率

        Returns:
            预测结果列表，每个元素包含 'type' 和可选的 'confidence'
        """
        if not self.use_ml or not self.is_trained:
            # 回退到规则分类
            return self._rule_based_predict(features)

        if not features:
            return []

        X = self._features_to_array(features)
        X_scaled = self.scaler.transform(X)

        if return_proba:
            # 返回概率
            proba = self.classifier.predict_proba(X_scaled)
            predictions = []
            for p in proba:
                idx = np.argmax(p)
                predictions.append(
                    {
                        "type": self.IDX_TO_CLASS[idx],
                        "confidence": float(p[idx]),
                    }
                )
            return predictions
        else:
            # 只返回类别
            predictions = self.classifier.predict(X_scaled)
            return [
                {"type": self.IDX_TO_CLASS[int(p)]} for p in predictions
            ]

    def _features_to_array(self, features: list[dict[str, Any]]) -> Any:
        """将特征字典列表转换为numpy数组"""
        if not SKLEARN_AVAILABLE or not features:
            return np.array([])

        # 获取所有特征的键（应该是一致的）
        feature_keys = sorted(features[0].keys())
        
        # 构建数组
        X = []
        for feat in features:
            row = [feat.get(key, 0.0) for key in feature_keys]
            X.append(row)

        return np.array(X, dtype=np.float32)

    def _rule_based_predict(
        self, features: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        基于规则的分类（回退方案）

        当ML模型不可用时使用启发式规则。
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

    def save_model(self, model_path: Path) -> None:
        """保存模型到文件"""
        if not self.use_ml or not self.is_trained:
            logger.warning("模型未训练，无法保存。")
            return

        model_data = {
            "classifier": self.classifier,
            "scaler": self.scaler,
            "class_labels": self.CLASS_LABELS,
        }

        with open(model_path, "wb") as f:
            pickle.dump(model_data, f)

        logger.info(f"模型已保存到: {model_path}")

    def load_model(self, model_path: Path) -> None:
        """从文件加载模型"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn 未安装，无法加载模型。")
            return

        try:
            with open(model_path, "rb") as f:
                model_data = pickle.load(f)

            self.classifier = model_data["classifier"]
            self.scaler = model_data["scaler"]
            self.is_trained = True

            logger.info(f"模型已从 {model_path} 加载")
        except Exception as e:
            logger.error(f"加载模型失败: {e}", exc_info=True)
            self.is_trained = False

    def get_feature_importance(self) -> dict[str, float]:
        """
        获取特征重要性（如果模型已训练）

        Returns:
            特征重要性字典
        """
        if not self.use_ml or not self.is_trained:
            return {}

        importances = self.classifier.feature_importances_
        # 这里需要知道特征名称的顺序
        # 由于特征是从字典转换的，我们需要在训练时保存特征顺序
        # 简化版：返回原始重要性数组的统计信息
        return {
            "mean_importance": float(np.mean(importances)),
            "max_importance": float(np.max(importances)),
            "min_importance": float(np.min(importances)),
        }

