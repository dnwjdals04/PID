# file_handler.py
import os
import mimetypes
from fastapi import UploadFile, HTTPException
from app.config import UPLOAD_DIR, ALLOWED_MIME, ALLOWED_EXT, MAX_BYTES

async def save_upload_file(file: UploadFile) -> str:
    """
    업로드된 파일을 검증하고 저장.
    같은 이름이 있으면 _1, _2 … 붙여서 저장.
    반환: 최종 저장 경로
    """
    ct = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    ext = os.path.splitext(file.filename or "")[1].lower()

    if ct and ct not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {ct}")
    if ext and ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"Unsupported extension: {ext}")

    # 중복 방지 이름 생성
    filename = os.path.basename(file.filename)
    path = os.path.join(UPLOAD_DIR, filename)
    base, ext = os.path.splitext(filename)
    i = 1
    while os.path.exists(path):
        filename = f"{base}_{i}{ext}"
        path = os.path.join(UPLOAD_DIR, filename)
        i += 1

    # 저장
    total = 0
    try:
        with open(path, "wb") as out:
            while chunk := await file.read(1024 * 1024):  # 1MB 단위
                total += len(chunk)
                if total > MAX_BYTES:
                    raise HTTPException(status_code=413, detail="File too large")
                out.write(chunk)
    finally:
        await file.close()

    return path
