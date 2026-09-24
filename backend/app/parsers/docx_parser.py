"""
CareerPilot AI — DOCX Parser
===============================
Extracts text from Microsoft Word .docx files using python-docx.

Why python-docx?
  - Official library for .docx (Office Open XML format)
  - Reads paragraphs, tables, headers
  - No Microsoft Office installation needed
"""

import io
from pathlib import Path
from typing import Union
import logging

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

logger = logging.getLogger(__name__)


class DOCXParser:
    """Parse text content from .docx files."""

    def parse_file(self, file_path: Union[str, Path]) -> str:
        try:
            with open(file_path, "rb") as f:
                return self.parse_bytes(f.read())
        except Exception as e:
            logger.error(f"Error parsing DOCX file {file_path}: {e}")
            return ""

    def parse_bytes(self, content: bytes) -> str:
        if not DOCX_AVAILABLE:
            raise RuntimeError("python-docx is not installed. Run: pip install python-docx")

        try:
            doc = Document(io.BytesIO(content))
            text_parts = []

            # Extract paragraph text
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    text_parts.append(text)

            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(
                        cell.text.strip() for cell in row.cells if cell.text.strip()
                    )
                    if row_text:
                        text_parts.append(row_text)

            return "\n".join(text_parts)

        except Exception as e:
            logger.error(f"Error parsing DOCX bytes: {e}")
            return ""


class TextParser:
    """Parse plain text files."""

    def parse_bytes(self, content: bytes) -> str:
        """Decode bytes to string, trying common encodings."""
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                return content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        return content.decode("utf-8", errors="replace")

    def parse_file(self, file_path: Union[str, Path]) -> str:
        try:
            with open(file_path, "rb") as f:
                return self.parse_bytes(f.read())
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            return ""


docx_parser = DOCXParser()
text_parser = TextParser()
