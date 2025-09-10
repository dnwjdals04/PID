#delete.py
import shutil
import os
from fastapi.responses import RedirectResponse
from fastapi import APIRouter
from app.config import UPLOAD_DIR, FRAME_DIR

router = APIRouter()

@router.post("/delete/{filename}")
async def delete_file(filename: str):
    video_filepath = os.path.join(UPLOAD_DIR, filename)

    # 1) 비디오 파일 삭제
    if os.path.exists(video_filepath) and os.path.isfile(video_filepath):
        os.remove(video_filepath)
    else:
        return {"error": f"Video file '{filename}' not found"}

    # 2) 프레임 디렉토리 삭제 (파일명 기반)
    name_without_ext = os.path.splitext(filename)[0]
    frame_dir = os.path.join(FRAME_DIR, name_without_ext)

    if os.path.exists(frame_dir):
        if os.path.isdir(frame_dir):
            shutil.rmtree(frame_dir)  # 디렉토리 전체 삭제
        elif os.path.isfile(frame_dir):
            os.remove(frame_dir)      # 혹시 파일로 잘못 생긴 경우
    # 없으면 그냥 패스

    # 3) 삭제 후 /files로 리다이렉트
    return RedirectResponse(url="/files", status_code=303)
