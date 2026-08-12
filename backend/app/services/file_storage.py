import hashlib, os, uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

MAX_RESUME_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.pdf': 'PDF', '.docx': 'DOCX'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}
STORAGE_ROOT = Path(os.getenv('UPLOAD_STORAGE_PATH', './storage/resumes'))


def _signature(data: bytes, ext: str) -> bool:
    return (
        data.startswith(b'%PDF-')
        if ext == '.pdf'
        else data.startswith(b'PK')
        if ext == '.docx'
        else False
    )


async def save_resume(upload: UploadFile) -> dict:
    original = Path(upload.filename or '').name
    ext = Path(original).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, 'Only PDF and DOCX resumes are allowed')

    if upload.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, 'Unsupported resume MIME type')

    size = 0
    sha = hashlib.sha256()
    data = bytearray()

    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_RESUME_SIZE:
            raise HTTPException(413, 'Resume exceeds 10 MB limit')
        sha.update(chunk)
        data.extend(chunk)

    if not data or not _signature(bytes(data[:8]), ext):
        raise HTTPException(400, 'File signature does not match extension')

    stored = f'{uuid.uuid4().hex}{ext}'
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    path = STORAGE_ROOT / stored
    path.write_bytes(data)

    return {
        'original_filename': original[:255],
        'stored_filename': stored,
        'file_type': ALLOWED_EXTENSIONS[ext],
        'mime_type': upload.content_type,
        'file_size': size,
        'sha256': sha.hexdigest(),
        'path': path,
    }