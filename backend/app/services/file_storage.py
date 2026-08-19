"""Uploaded resume validation and storage.

1. Extension allow-list -- only '.pdf' and '.docx'.
2. Declared MIME allow-list -- client-supplied, so necessary but not
   sufficient.
3. Magic-byte check -- the real format, since 'content_type' is trivially
   faked.
4. Pre-allocation-aware compressed size checks on .docx (decompression bomb defense).
5. Streaming size cap -- bounds byte count before entire payload hits memory.
6. Generated storage filenames -- a UUID, never the client's name, so path
   traversal and overwrite are impossible by construction.
"""

from __future__ import annotations

import hashlib
from io import BytesIO
import logging
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final, NoReturn

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS: Final[dict[str, str]] = {".pdf": "PDF", ".docx": "DOCX"}

ALLOWED_MIME_TYPES: Final[frozenset[str]] = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)

# Magic bytes per extension. DOCX is a ZIP container, hence 'PK\x03\x04'.
SIGNATURES: Final[dict[str, tuple[bytes, ...]]] = {
    ".pdf": (b"%PDF-",),
    ".docx": (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),
}

READ_CHUNK_SIZE: Final = 1024 * 1024

# A legitimate DOCX compresses maybe 10-20x. Beyond this is a decompression
# bomb rather than a resume.
MAX_DECOMPRESSION_RATIO: Final = 100
MAX_UNCOMPRESSED_BYTES: Final = 200 * 1024 * 1024

# A resume with thousands of archive members is not a resume.
MAX_ARCHIVE_MEMBERS: Final = 400


@dataclass(frozen=True, slots=True)
class StoredResume:
    """Metadata for a validated, stored upload.

    A typed result rather than the previous untyped 'dict', so a caller cannot
    misspell a key and silently persist 'None'.
    """

    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    sha256: str
    path: Path

    def as_model_kwargs(self) -> dict[str, object]:
        """Fields that map directly onto the 'Resume' model."""
        return {
            "original_filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "file_type": self.file_type,
            "mime_type": self.file_type or "application/octet-stream",
            "file_size": self.file_size,
            "sha256": self.sha256,
        }


def _reject(message: str, *, code: int = status.HTTP_400_BAD_REQUEST) -> NoReturn:
    """Raise a client error without echoing attacker-controlled content back."""
    raise HTTPException(status_code=code, detail=message)


def _storage_root() -> Path:
    return Path(settings.UPLOAD_STORAGE_PATH)


def _validate_signature(header: bytes, extension: str) -> bool:
    return any(header.startswith(magic) for magic in SIGNATURES[extension])


def _validate_docx_archive(data: bytes) -> None:
    """Reject DOCX archives that are malformed or decompression bombs.

    Sizes are read from the ZIP central directory, so nothing is inflated in
    order to perform this check.
    """
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            members = archive.infolist()

            if len(members) > MAX_ARCHIVE_MEMBERS:
                _reject("Resume archive contains too many entries")

            total_uncompressed = sum(member.file_size for member in members)
            if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
                _reject("Resume archive expands to an unreasonable size")

            compressed = max(1, len(data))
            if total_uncompressed / compressed > MAX_DECOMPRESSION_RATIO:
                logger.warning(
                    "Rejected upload: compression ratio %.1fx exceeds limit",
                    total_uncompressed / compressed,
                )
                _reject("Resume archive has a suspicious compression ratio")

            # A real .docx always contains the main document part.
            if not any(
                member.filename == "word/document.xml" for member in members
            ):
                _reject("File is not a valid DOCX document")
    except zipfile.BadZipFile:
        _reject("File is not a readable DOCX document")


async def save_resume(upload: UploadFile) -> StoredResume:
    """Validate and persist an uploaded resume.

    Raises 'HTTPException' for anything that fails validation. The file is only
    written to disk once every check has passed.
    """
    # Path(...).name strips any directory component the client supplied.
    original = Path(upload.filename or "").name
    extension = Path(original).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        _reject("Only PDF and DOCX resumes are allowed")

    if upload.content_type not in ALLOWED_MIME_TYPES:
        _reject("Unsupported resume MIME type")

    max_bytes = settings.max_resume_size_bytes
    digest = hashlib.sha256()
    buffer = bytearray()
    size = 0

    while True:
        chunk = await upload.read(READ_CHUNK_SIZE)
        if not chunk:
            break

        size += len(chunk)
        if size > max_bytes:
            # Stop reading immediately rather than buffering the whole payload.
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Resume exceeds the {settings.MAX_RESUME_SIZE_MB} MB limit",
            )

        digest.update(chunk)
        buffer.extend(chunk)

    if not buffer:
        _reject("Resume file is empty")

    if not _validate_signature(bytes(buffer[:8]), extension):
        logger.warning(
            "Rejected upload: content does not match its extension",
        )
        _reject("File signature does not match its extension")

    if extension == ".docx":
        _validate_docx_archive(bytes(buffer))

    stored_filename = f"{uuid.uuid4().hex}{extension}"
    root = _storage_root()
    root.mkdir(parents=True, exist_ok=True)
    path = root / stored_filename

    # resolve() plus a containment assertion guards against a symlinked or
    # traversal-configured storage root.
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    if not resolved_path.is_relative_to(resolved_root):
        logger.error("Refusing to write outside the storage root %s", resolved_root)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage configuration error",
        )

    path.write_bytes(buffer)

    logger.info(
        "Stored %s resume (%d bytes)", ALLOWED_EXTENSIONS[extension], size
    )

    return StoredResume(
        original_filename=original[:255],
        stored_filename=stored_filename,
        file_type=ALLOWED_EXTENSIONS[extension],
        mime_type=upload.content_type or "application/octet-stream",
        file_size=size,
        sha256=digest.hexdigest(),
        path=path,
    )


def delete_stored_resume(path: Path) -> None:
    """Remove a stored file, tolerating its absence."""
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not remove stored resume", exc_info=True)