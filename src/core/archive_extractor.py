import zipfile
import tempfile
import os
import subprocess
from pathlib import Path
from tika import parser
from typing import Dict


class ArchiveExtractor:
    """
    Extracts ONLY PDF files from ZIP archives
    Uses Apache Tika + OCR fallback for scanned PDFs
    """

    def extract_documents(self, zip_path: Path):
        if not str(zip_path).lower().endswith(".zip"):
            raise ValueError(f"Not a zip file: {zip_path}")

        documents = []

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for member in zip_ref.namelist():

                if not self._is_pdf(member):
                    continue

                with zip_ref.open(member) as f, tempfile.NamedTemporaryFile(
                    suffix=".pdf", delete=False
                ) as tmp:
                    tmp.write(f.read())
                    tmp_path = tmp.name

                try:
                    parsed = self._extract_with_tika(tmp_path)

                    ocr_applied = False

                    # 🔁 OCR fallback if Tika text is empty
                    if not parsed["content"].strip():
                        text = self._extract_text_via_ocr_and_tika(tmp_path)
                        if text:
                            parsed["content"] = text
                            ocr_applied = True

                    if parsed["content"].strip():
                        metadata = parsed["metadata"]
                        metadata["ocr_applied"] = ocr_applied

                        documents.append({
                            "content": parsed["content"],
                            "metadata": metadata,
                            "source": member  # logical ZIP path
                        })

                finally:
                    os.remove(tmp_path)

        return documents

    # --------------------------------------------------

    def _is_pdf(self, filename: str) -> bool:
        return (
            Path(filename).suffix.lower() == ".pdf"
            and not filename.startswith("__MACOSX")
            and not Path(filename).name.startswith(".")
        )

    # --------------------------------------------------

    def _extract_with_tika(self, file_path: str) -> Dict:
        parsed = parser.from_file(file_path)

        return {
            "content": self._clean_content(parsed.get("content", "") or ""),
            "metadata": parsed.get("metadata", {}) or {}
        }

    # --------------------------------------------------

    def _extract_text_via_ocr_and_tika(self, input_pdf: str) -> str:
        """
        OCR using ocrmypdf → parse with Tika
        """

        temp_pdf_path = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False
            ) as tmp:
                temp_pdf_path = tmp.name

            cmd = [
                "ocrmypdf",
                "--deskew",
                "--rotate-pages",
                "--optimize", "3",
                "--skip-text",
                input_pdf,
                temp_pdf_path
            ]

            subprocess.run(cmd, check=True)

            parsed = parser.from_file(temp_pdf_path)
            return self._clean_content(parsed.get("content", "") or "")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"OCR failed: {e}")

        finally:
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

    # --------------------------------------------------

    def _clean_content(self, text: str) -> str:
        import re
        text = re.sub(r"\n+", "\n", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
