import os, uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from .database import get_db
from . import models
from .security import get_current_user
from .worker import process_document

router = APIRouter(prefix="/documents", tags=["documents"])
UPLOAD_DIR = "/uploads"
MAX_BYTES = 20 * 1024 * 1024

@router.post("", status_code=201)
async def upload(file: UploadFile = File(...),
                 user: models.User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "File too large (max 20 MB)")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}.pdf")
    with open(path, "wb") as f:
        f.write(data)
    doc = models.Document(user_id=user.id, filename=file.filename, status="uploaded")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    process_document.delay(doc.id, path)
    return {"id": doc.id, "filename": doc.filename, "status": doc.status}

@router.get("")
def list_documents(user: models.User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    docs = (db.query(models.Document).filter_by(user_id=user.id)
            .order_by(models.Document.created_at.desc()).all())
    return [{"id": d.id, "filename": d.filename, "status": d.status,
             "page_count": d.page_count} for d in docs]

@router.get("/{doc_id}")
def get_document(doc_id: int, user: models.User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    d = db.get(models.Document, doc_id)
    if not d or d.user_id != user.id:
        raise HTTPException(404, "Document not found")
    return {"id": d.id, "filename": d.filename, "status": d.status,
            "page_count": d.page_count}
