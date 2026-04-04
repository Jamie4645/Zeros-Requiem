"""
PDF Parser — extracts text and detects visual/chart pages from trading book PDFs.
Used by Claude Code to read books page by page.
"""

import fitz  # PyMuPDF
import os
from pathlib import Path


class PDFParser:
    VISUAL_PAGE_TEXT_THRESHOLD = 100

    def parse(self, pdf_path: str) -> dict:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(pdf_path)

        metadata = {
            "title": doc.metadata.get("title", Path(pdf_path).stem),
            "author": doc.metadata.get("author", "Unknown"),
            "page_count": len(doc),
            "file_name": Path(pdf_path).name,
            "file_path": pdf_path,
        }

        pages = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            word_count = len(text.split())
            image_list = page.get_images(full=True)
            is_visual = (
                len(image_list) > 0
                or len(text.strip()) < self.VISUAL_PAGE_TEXT_THRESHOLD
            )
            pages.append({
                "page_num": page_num + 1,
                "text": text,
                "is_visual": is_visual,
                "word_count": word_count,
                "image_count": len(image_list),
            })

        doc.close()
        return {"metadata": metadata, "pages": pages}

    def extract_text_chunks(self, pages: list, chunk_size: int = 15) -> list:
        chunks = []
        for i in range(0, len(pages), chunk_size):
            chunk_pages = pages[i:i + chunk_size]
            combined_text = "\n\n".join(
                f"--- PAGE {p['page_num']} ---\n{p['text']}"
                for p in chunk_pages
            )
            chunks.append({
                "chunk_index": len(chunks),
                "start_page": chunk_pages[0]["page_num"],
                "end_page": chunk_pages[-1]["page_num"],
                "text": combined_text,
                "total_words": sum(p["word_count"] for p in chunk_pages),
                "visual_pages": [p["page_num"] for p in chunk_pages if p["is_visual"]],
            })
        return chunks

    def get_table_of_contents(self, pdf_path: str) -> list:
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()
        doc.close()
        return [{"level": e[0], "title": e[1], "page": e[2]} for e in toc]
