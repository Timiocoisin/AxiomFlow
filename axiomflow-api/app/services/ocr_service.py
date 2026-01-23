"""
OCR服务模块

支持多种OCR引擎：
- Tesseract OCR（默认，开源且广泛支持）
- EasyOCR（可选，准确率较高）
- PaddleOCR（可选，对中文支持好）

自动检测扫描版PDF并进行OCR识别。
"""

from __future__ import annotations

import io
import logging
import tempfile
from pathlib import Path
from typing import Any
from dataclasses import dataclass

import fitz  # PyMuPDF
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

# OCR引擎可用性标志
TESSERACT_AVAILABLE = False
EASYOCR_AVAILABLE = False
PADDLEOCR_AVAILABLE = False

# 尝试导入Tesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    logger.warning("pytesseract not installed, Tesseract OCR will be disabled.")

# 尝试导入EasyOCR
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    logger.debug("easyocr not installed, EasyOCR will be disabled.")

# 尝试导入PaddleOCR
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    logger.debug("paddleocr not installed, PaddleOCR will be disabled.")


@dataclass
class OCRResult:
    """OCR识别结果"""
    text: str
    confidence: float
    bbox: tuple[float, float, float, float] | None = None
    words: list[dict[str, Any]] | None = None  # 单词级别的详细信息


def is_scanned_pdf(pdf_path: Path | str, page_index: int = 0, threshold: float = 0.1) -> bool:
    """
    检测PDF是否为扫描版
    
    Args:
        pdf_path: PDF文件路径
        page_index: 要检测的页面索引（默认第一页）
        threshold: 文本比例阈值，低于此值视为扫描版
    
    Returns:
        True表示扫描版，False表示文本版
    """
    try:
        doc = fitz.open(pdf_path)
        if page_index >= doc.page_count:
            page_index = 0
        
        page = doc.load_page(page_index)
        
        # 获取页面文本
        text = page.get_text()
        text_length = len(text.strip())
        
        # 获取页面大小
        rect = page.rect
        
        # 如果文本长度很少，可能是扫描版
        # 计算文本密度（文本长度 / 页面面积）
        page_area = rect.width * rect.height
        text_density = text_length / max(page_area, 1.0) * 1000  # 归一化
        
        doc.close()
        
        # 文本密度低于阈值，视为扫描版
        is_scanned = text_density < threshold
        
        logger.debug(f"PDF扫描检测: text_density={text_density:.4f}, threshold={threshold}, is_scanned={is_scanned}")
        
        return is_scanned
    except Exception as e:
        logger.error(f"检测扫描PDF时出错: {e}")
        # 默认返回False，继续尝试文本提取
        return False


class TesseractOCREngine:
    """Tesseract OCR引擎"""
    
    def __init__(self, lang: str = "eng+chi_sim"):
        """
        初始化Tesseract OCR引擎
        
        Args:
            lang: 语言代码，多个语言用+连接（如 "eng+chi_sim" 表示英文+简体中文）
        """
        self.lang = lang
        self._available = TESSERACT_AVAILABLE
        if not self._available:
            logger.warning("Tesseract OCR不可用，请安装 pytesseract 和 Tesseract")
    
    def is_available(self) -> bool:
        return self._available
    
    def recognize(self, image: Image.Image | np.ndarray) -> OCRResult:
        """
        识别图像中的文本
        
        Args:
            image: PIL Image 或 numpy array
        
        Returns:
            OCRResult对象
        """
        if not self._available:
            raise RuntimeError("Tesseract OCR不可用")
        
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # 使用Tesseract进行OCR
        try:
            # 获取详细信息（包括边界框）
            data = pytesseract.image_to_data(image, lang=self.lang, output_type=pytesseract.Output.DICT)
            
            # 提取文本和置信度
            texts = []
            confidences = []
            words = []
            
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if text:
                    conf = float(data['conf'][i]) if data['conf'][i] != -1 else 0.0
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    
                    texts.append(text)
                    confidences.append(conf)
                    words.append({
                        'text': text,
                        'confidence': conf,
                        'bbox': (x, y, x + w, y + h),
                    })
            
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                words=words if words else None,
            )
        except Exception as e:
            logger.error(f"Tesseract OCR识别失败: {e}")
            return OCRResult(text="", confidence=0.0)


class EasyOCREngine:
    """EasyOCR引擎"""
    
    def __init__(self, lang: list[str] = None):
        """
        初始化EasyOCR引擎
        
        Args:
            lang: 语言列表，如 ['en', 'ch_sim']（英文和简体中文）
        """
        if lang is None:
            lang = ['en', 'ch_sim']
        self.lang = lang
        self._available = EASYOCR_AVAILABLE
        self._reader = None
        
        if self._available:
            try:
                # 初始化reader（首次调用会下载模型，较慢）
                logger.info("正在初始化EasyOCR引擎（首次使用可能需要下载模型）...")
                self._reader = easyocr.Reader(self.lang, gpu=False)  # CPU模式
                logger.info("EasyOCR引擎初始化完成")
            except Exception as e:
                logger.error(f"EasyOCR初始化失败: {e}")
                self._available = False
        else:
            logger.warning("EasyOCR不可用，请安装 easyocr")
    
    def is_available(self) -> bool:
        return self._available and self._reader is not None
    
    def recognize(self, image: Image.Image | np.ndarray) -> OCRResult:
        """
        识别图像中的文本
        
        Args:
            image: PIL Image 或 numpy array
        
        Returns:
            OCRResult对象
        """
        if not self.is_available():
            raise RuntimeError("EasyOCR不可用")
        
        if isinstance(image, Image.Image):
            image = np.array(image)
        
        try:
            # EasyOCR返回 [(bbox, text, confidence), ...]
            results = self._reader.readtext(image)
            
            texts = []
            confidences = []
            words = []
            
            for bbox, text, confidence in results:
                texts.append(text)
                confidences.append(float(confidence))
                
                # 计算边界框
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                x0 = min(x_coords)
                y0 = min(y_coords)
                x1 = max(x_coords)
                y1 = max(y_coords)
                
                words.append({
                    'text': text,
                    'confidence': float(confidence),
                    'bbox': (x0, y0, x1, y1),
                })
            
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                words=words if words else None,
            )
        except Exception as e:
            logger.error(f"EasyOCR识别失败: {e}")
            return OCRResult(text="", confidence=0.0)


class PaddleOCREngine:
    """PaddleOCR引擎"""
    
    def __init__(self, lang: str = "ch"):
        """
        初始化PaddleOCR引擎
        
        Args:
            lang: 语言代码，如 'ch'（中文）、'en'（英文）
        """
        self.lang = lang
        self._available = PADDLEOCR_AVAILABLE
        self._ocr = None
        
        if self._available:
            try:
                logger.info("正在初始化PaddleOCR引擎（首次使用可能需要下载模型）...")
                self._ocr = PaddleOCR(use_angle_cls=True, lang=self.lang, use_gpu=False)  # CPU模式
                logger.info("PaddleOCR引擎初始化完成")
            except Exception as e:
                logger.error(f"PaddleOCR初始化失败: {e}")
                self._available = False
        else:
            logger.warning("PaddleOCR不可用，请安装 paddleocr")
    
    def is_available(self) -> bool:
        return self._available and self._ocr is not None
    
    def recognize(self, image: Image.Image | np.ndarray) -> OCRResult:
        """
        识别图像中的文本
        
        Args:
            image: PIL Image 或 numpy array
        
        Returns:
            OCRResult对象
        """
        if not self.is_available():
            raise RuntimeError("PaddleOCR不可用")
        
        if isinstance(image, Image.Image):
            image = np.array(image)
        
        try:
            # PaddleOCR返回 [[[bbox], (text, confidence)], ...]
            results = self._ocr.ocr(image, cls=True)
            
            texts = []
            confidences = []
            words = []
            
            if results and results[0]:
                for line in results[0]:
                    if line:
                        bbox, (text, confidence) = line
                        texts.append(text)
                        confidences.append(float(confidence))
                        
                        # 计算边界框
                        x_coords = [point[0] for point in bbox]
                        y_coords = [point[1] for point in bbox]
                        x0 = min(x_coords)
                        y0 = min(y_coords)
                        x1 = max(x_coords)
                        y1 = max(y_coords)
                        
                        words.append({
                            'text': text,
                            'confidence': float(confidence),
                            'bbox': (x0, y0, x1, y1),
                        })
            
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                words=words if words else None,
            )
        except Exception as e:
            logger.error(f"PaddleOCR识别失败: {e}")
            return OCRResult(text="", confidence=0.0)


class OCRService:
    """OCR服务管理器"""
    
    def __init__(self, engine: str = "auto", lang: str = "eng+chi_sim"):
        """
        初始化OCR服务
        
        Args:
            engine: OCR引擎类型（"tesseract", "easyocr", "paddleocr", "auto"）
            lang: 语言代码（Tesseract格式）
        """
        self.engine_type = engine
        self.lang = lang
        self._tesseract = None
        self._easyocr = None
        self._paddleocr = None
        
        # 初始化可用的引擎
        if TESSERACT_AVAILABLE:
            self._tesseract = TesseractOCREngine(lang=lang)
        
        if EASYOCR_AVAILABLE:
            try:
                # EasyOCR使用不同的语言代码
                lang_map = {'chi_sim': 'ch_sim', 'chi_tra': 'ch_tra'}
                easyocr_langs = []
                for l in lang.split('+'):
                    easyocr_langs.append(lang_map.get(l, l))
                self._easyocr = EasyOCREngine(lang=easyocr_langs)
            except Exception:
                pass
        
        if PADDLEOCR_AVAILABLE:
            try:
                # PaddleOCR使用不同的语言代码
                paddle_lang = 'ch' if 'chi' in lang.lower() else 'en'
                self._paddleocr = PaddleOCREngine(lang=paddle_lang)
            except Exception:
                pass
        
        # 自动选择最佳引擎
        if engine == "auto":
            if self._tesseract and self._tesseract.is_available():
                self.engine = self._tesseract
                logger.info("自动选择Tesseract OCR引擎")
            elif self._easyocr and self._easyocr.is_available():
                self.engine = self._easyocr
                logger.info("自动选择EasyOCR引擎")
            elif self._paddleocr and self._paddleocr.is_available():
                self.engine = self._paddleocr
                logger.info("自动选择PaddleOCR引擎")
            else:
                raise RuntimeError("没有可用的OCR引擎，请安装 pytesseract、easyocr 或 paddleocr")
        elif engine == "tesseract":
            if not self._tesseract or not self._tesseract.is_available():
                raise RuntimeError("Tesseract OCR不可用")
            self.engine = self._tesseract
        elif engine == "easyocr":
            if not self._easyocr or not self._easyocr.is_available():
                raise RuntimeError("EasyOCR不可用")
            self.engine = self._easyocr
        elif engine == "paddleocr":
            if not self._paddleocr or not self._paddleocr.is_available():
                raise RuntimeError("PaddleOCR不可用")
            self.engine = self._paddleocr
        else:
            raise ValueError(f"未知的OCR引擎: {engine}")
    
    def recognize_page(self, pdf_path: Path | str, page_index: int, dpi: int = 300) -> OCRResult:
        """
        识别PDF页面中的文本
        
        Args:
            pdf_path: PDF文件路径
            page_index: 页面索引（从0开始）
            dpi: 渲染DPI（默认300，越高越准确但越慢）
        
        Returns:
            OCRResult对象
        """
        try:
            doc = fitz.open(pdf_path)
            if page_index >= doc.page_count:
                raise ValueError(f"页面索引 {page_index} 超出范围（总页数: {doc.page_count}）")
            
            page = doc.load_page(page_index)
            
            # 将页面渲染为图像
            mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72是默认DPI
            pix = page.get_pixmap(matrix=mat)
            
            # 转换为PIL Image
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            doc.close()
            
            # 执行OCR
            result = self.engine.recognize(image)
            
            return result
        except Exception as e:
            logger.error(f"OCR识别页面失败: {e}")
            return OCRResult(text="", confidence=0.0)
    
    def recognize_image(self, image: Image.Image | np.ndarray) -> OCRResult:
        """
        识别图像中的文本
        
        Args:
            image: PIL Image 或 numpy array
        
        Returns:
            OCRResult对象
        """
        return self.engine.recognize(image)


# 全局OCR服务实例（懒加载）
_ocr_service: OCRService | None = None


def get_ocr_service(engine: str = "auto", lang: str = "eng+chi_sim") -> OCRService:
    """
    获取OCR服务实例（单例模式）
    
    Args:
        engine: OCR引擎类型
        lang: 语言代码
    
    Returns:
        OCRService实例
    """
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService(engine=engine, lang=lang)
    return _ocr_service

