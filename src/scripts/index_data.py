import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core.vector_store import vectorstore
from src.core.archive_extractor import ArchiveExtractor
from src.config import Config

# ----------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

# ----------------------------------------------------

def build_metadata_from_tika(
    tika_meta: dict,
    source_path: str,
    archive_name: str | None = None
) -> dict:
    """
    source_path example:
    Supporting Document Attachments/TX Transmittal lah311.pdf

    archive_name example:
    NALF-131770385.zip
    """

    # Derive top-level folder name from archive
    # e.g. NALF-131770385.zip → NALF-131770385
    root_folder = archive_name.replace(".zip", "") if archive_name else None

    # Build full logical path
    if root_folder:
        full_source_path = f"{root_folder}/{source_path}"
        print(full_source_path)
    else:
        full_source_path = source_path

    return {
        # FULL LOGICAL PATH (what you want)
        "source": full_source_path,

        # Optional but useful
        "relative_path": source_path,
        "pdf_filename": os.path.basename(source_path),
        "archive_name": archive_name,
        "file_type": ".pdf",

        # TIKA METADATA
        "producer": tika_meta.get("pdf:producer"),
        "creator": tika_meta.get("dc:creator") or tika_meta.get("pdf:docinfo:creator"),
        "title": tika_meta.get("dc:title"),
        "creation_date": tika_meta.get("dcterms:created"),
        "modification_date": tika_meta.get("dcterms:modified"),
        "total_pages": int(tika_meta["xmpTPg:NPages"])
            if tika_meta.get("xmpTPg:NPages") else None,

        # OCR FLAG
        "ocr_applied": tika_meta.get("ocr_applied", False),

        "indexed_at": datetime.utcnow().isoformat()
    }

# ----------------------------------------------------

def index_zip_archive(zip_path: Path) -> dict:
    """
    Index one ZIP archive
    Returns stats for reporting
    """

    extractor = ArchiveExtractor()
    archive_name = zip_path.name

    print(f"\n📦 Processing archive: {archive_name}")

    extracted_docs = extractor.extract_documents(zip_path)

    total_pdfs = len(extracted_docs)
    ocr_pdfs = sum(
        1 for d in extracted_docs
        if d["metadata"].get("ocr_applied") is True
    )

    if not extracted_docs:
        print("   ⚠ No PDFs extracted")
        return {
            "pdfs": 0,
            "ocr_pdfs": 0,
            "chunks": 0
        }

    print(f"   📄 PDFs found: {total_pdfs}")
    print(f"   🔍 OCR applied to: {ocr_pdfs}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP,
        length_function=len
    )

    total_chunks = 0

    for doc in extracted_docs:
        content = doc["content"]

        documents = [Document(page_content=content)]

        chunks = splitter.split_documents(documents)

        docs_to_index = []
        for chunk in chunks:
            docs_to_index.append({
                "page_content": chunk.page_content,
                "metadata": build_metadata_from_tika(
                    tika_meta=doc["metadata"],
                    source_path=doc["source"],      # ZIP internal path
                    archive_name=archive_name
                )
            })

        count = vectorstore.add_documents(docs_to_index)
        total_chunks += count

    print(f"   ✅ Indexed {total_chunks} chunks")

    return {
        "pdfs": total_pdfs,
        "ocr_pdfs": ocr_pdfs,
        "chunks": total_chunks
    }

# ----------------------------------------------------

def main():
    print("\n" + "=" * 80)
    print("RAG DOCUMENT INDEXING PIPELINE")
    print("=" * 80)

    vectorstore.create_index_if_not_exists()

    pdf_collection_dir = BASE_DIR / "src" / "pdf_collection"

    if not pdf_collection_dir.exists():
        print(f"✗ Directory not found: {pdf_collection_dir}")
        return

    zip_files = list(pdf_collection_dir.rglob("*.zip"))

    if not zip_files:
        print("No ZIP files found")
        return

    grand_total_chunks = 0
    grand_total_pdfs = 0
    grand_total_ocr = 0

    for zip_path in zip_files:
        stats = index_zip_archive(zip_path)

        grand_total_pdfs += stats["pdfs"]
        grand_total_ocr += stats["ocr_pdfs"]
        grand_total_chunks += stats["chunks"]

    print("\n" + "=" * 80)
    print("✅ INDEXING COMPLETE")
    print("=" * 80)
    print(f"📄 Total PDFs indexed: {grand_total_pdfs}")
    print(f"🔍 OCR PDFs: {grand_total_ocr}")
    print(f"🧩 Total chunks indexed: {grand_total_chunks}")

    stats = vectorstore.get_index_stats()
    print("\n📊 ELASTICSEARCH STATS")
    print(f"Documents: {stats.get('document_count', 0)}")
    print(f"Index size: {stats.get('size_mb', 0)} MB")
    print("=" * 80)

# ----------------------------------------------------

if __name__ == "__main__":
    main()
