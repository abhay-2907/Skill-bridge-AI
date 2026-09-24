"""
CareerPilot AI — PDF Parser
==============================
What is this?
  Extracts raw text from PDF files using pypdf.

Why pypdf?
  - Pure Python (no external binary dependencies)
  - Handles most PDF formats
  - No pdftotext or Ghostscript needed

Limitations:
  - Scanned PDFs (images) produce empty/garbage text
  - Complex multi-column layouts may lose formatting
  - Tables may not parse cleanly
  - PDFs with custom fonts may show encoding issues

Interview questions:
  Q: How would you handle scanned/image PDFs?
  A: Use OCR (Optical Character Recognition) with libraries like
     pytesseract (Tesseract OCR) or cloud OCR APIs.
     You'd convert each PDF page to an image, then run OCR.
"""

import io
from pathlib import Path
from typing import Union
import logging

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFParser:
    """Parse text content from PDF files."""

    MAX_PAGES = 20  # Limit to prevent abuse

    def parse_file(self, file_path: Union[str, Path]) -> str:
        """
        Extract text from a PDF file on disk.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text as a string, or empty string on failure
        """
        if not PYPDF_AVAILABLE:
            raise RuntimeError("pypdf is not installed. Run: pip install pypdf")

        try:
            with open(file_path, "rb") as f:
                return self.parse_bytes(f.read())
        except FileNotFoundError:
            logger.error(f"PDF file not found: {file_path}")
            return ""
        except Exception as e:
            logger.error(f"Error parsing PDF file {file_path}: {e}")
            return ""

    def parse_bytes(self, content: bytes) -> str:
        """
        Extract text from PDF bytes (e.g., from an upload).

        Args:
            content: Raw PDF bytes

        Returns:
            Extracted text as a string
        """
        if not PYPDF_AVAILABLE:
            raise RuntimeError("pypdf is not installed. Run: pip install pypdf")

        try:
            reader = PdfReader(io.BytesIO(content))
            pages_text = []

            page_count = min(len(reader.pages), self.MAX_PAGES)
            for page_num in range(page_count):
                try:
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                except Exception as e:
                    logger.warning(f"Could not extract text from page {page_num}: {e}")
                    continue

            full_text = "\n".join(pages_text)

            if not full_text.strip():
                logger.warning("PDF appears to be empty or image-based (no extractable text)")
                return ""

            return full_text

        except Exception as e:
            logger.error(f"Error parsing PDF bytes: {e}")
            return ""

    def is_likely_scanned(self, content: bytes) -> bool:
        """
        Heuristic check: if extracted text is very short relative to page count,
        the PDF is likely image-based (scanned).
        """
        try:
            reader = PdfReader(io.BytesIO(content))
            text = ""
            for page in reader.pages[:3]:
                extracted = page.extract_text()
                if extracted:
                    text += extracted

            # If we have pages but almost no text, it's likely scanned
            return len(reader.pages) > 0 and len(text.strip()) < 100
        except Exception:
            return False


pdf_parser = PDFParser()
