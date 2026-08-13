"""
Image and Document Conversion Helpers.
Converts PDF pages, JPG, PNG, TIFF files to OpenCV BGR numpy arrays,
and converts OpenCV images to PySide6 QImage/QPixmap for GUI display.
"""

import os
import cv2
import numpy as np
from PySide6.QtGui import QImage, QPixmap

try:
    import pypdfium2 as pdfium
    HAS_PDFIUM = True
except ImportError:
    HAS_PDFIUM = False


def load_file_to_cv2_images(file_path: str) -> list[tuple[int, np.ndarray]]:
    """
    Loads an image file (JPG, PNG, TIFF) or multi-page PDF file into OpenCV BGR numpy images.
    Returns: list of tuples (page_index, cv2_bgr_image)
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext in ['.pdf']:
        if not HAS_PDFIUM:
            raise RuntimeError("pypdfium2 is required for processing PDF files.")

        pdf = pdfium.PdfDocument(file_path)
        images = []
        for i, page in enumerate(pdf):
            # Render page at 200 DPI for optimal speed and precision
            bitmap = page.render(scale=2.0)
            pil_image = bitmap.to_pil()
            bgr_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            images.append((i + 1, bgr_image))
        return images
    else:
        # Standard image file
        image = cv2.imread(file_path)
        if image is None:
            raise ValueError(f"Could not load image file: {file_path}")
        return [(1, image)]


def cv2_to_qpixmap(cv_img: np.ndarray) -> QPixmap:
    """Converts OpenCV BGR image to PySide6 QPixmap."""
    if cv_img is None:
        return QPixmap()

    height, width = cv_img.shape[:2]

    if len(cv_img.shape) == 2:
        # Grayscale
        q_img = QImage(cv_img.data, width, height, width, QImage.Format_Grayscale8)
    else:
        # BGR to RGB
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        bytes_per_line = 3 * width
        q_img = QImage(rgb_img.data, width, height, bytes_per_line, QImage.Format_RGB888)

    return QPixmap.fromImage(q_img)
