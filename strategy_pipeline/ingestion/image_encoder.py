"""
Image Encoder — rasterizes PDF pages with charts/diagrams into images
so Claude Code can visually read candlestick patterns, indicator overlays, etc.
"""

import base64
import io
import fitz
from PIL import Image


class ImageEncoder:
    DEFAULT_DPI = 200
    MAX_DIMENSION = 1568
    JPEG_QUALITY = 85

    def encode_visual_pages(self, pages: list, pdf_path: str, dpi: int = None) -> list:
        dpi = dpi or self.DEFAULT_DPI
        visual_pages = [p for p in pages if p.get("is_visual")]
        if not visual_pages:
            return []

        doc = fitz.open(pdf_path)
        encoded = []

        for page_info in visual_pages:
            page_num = page_info["page_num"] - 1
            if page_num >= len(doc):
                continue

            page = doc[page_num]
            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix)

            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            img = self._resize_if_needed(img)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=self.JPEG_QUALITY)
            buffer.seek(0)

            b64 = base64.standard_b64encode(buffer.read()).decode("utf-8")
            encoded.append({
                "page_num": page_info["page_num"],
                "base64_data": b64,
                "media_type": "image/jpeg",
                "width": img.width,
                "height": img.height,
                "text_on_page": page_info.get("text", ""),
            })

        doc.close()
        return encoded

    def encode_specific_pages(self, pdf_path: str, page_numbers: list, dpi: int = None) -> list:
        dpi = dpi or self.DEFAULT_DPI
        doc = fitz.open(pdf_path)
        encoded = []

        for page_num in page_numbers:
            idx = page_num - 1
            if idx < 0 or idx >= len(doc):
                continue
            page = doc[idx]
            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix)

            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            img = self._resize_if_needed(img)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=self.JPEG_QUALITY)
            buffer.seek(0)

            b64 = base64.standard_b64encode(buffer.read()).decode("utf-8")
            encoded.append({
                "page_num": page_num,
                "base64_data": b64,
                "media_type": "image/jpeg",
                "width": img.width,
                "height": img.height,
            })

        doc.close()
        return encoded

    def _resize_if_needed(self, img):
        w, h = img.size
        if max(w, h) <= self.MAX_DIMENSION:
            return img
        if w > h:
            new_w = self.MAX_DIMENSION
            new_h = int(h * (self.MAX_DIMENSION / w))
        else:
            new_h = self.MAX_DIMENSION
            new_w = int(w * (self.MAX_DIMENSION / h))
        return img.resize((new_w, new_h), Image.LANCZOS)
