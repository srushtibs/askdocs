import fitz  # PyMuPDF
from celery import Celery
from .config import settings
from .database import SessionLocal
from . import models
from .chunking import chunk_text
from .embeddings import embed_texts

celery_app = Celery("askdocs", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

@celery_app.task(name="process_document")
def process_document(document_id: int, path: str):
    db = SessionLocal()
    try:
        doc = db.get(models.Document, document_id)
        doc.status = "processing"
        db.commit()

        pdf = fitz.open(path)
        doc.page_count = len(pdf)
        pieces = []  # (page_number, text)
        for page_num, page in enumerate(pdf, start=1):
            for c in chunk_text(page.get_text()):
                pieces.append((page_num, c))
        pdf.close()

        if not pieces:
            raise ValueError("No extractable text (scanned PDF?)")

        vectors = embed_texts([p[1] for p in pieces])
        for (page_num, content), vec in zip(pieces, vectors):
            db.add(models.Chunk(document_id=doc.id, page_number=page_num,
                                content=content, embedding=vec))
        doc.status = "ready"
        db.commit()
    except Exception as e:
        db.rollback()
        doc = db.get(models.Document, document_id)
        doc.status = "failed"
        db.commit()
        print(f"process_document failed: {e}")
    finally:
        db.close()
