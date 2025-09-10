from fastapi import APIRouter, UploadFile, File, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from app.utils.file_handler import save_upload_file
from app.utils.media_utils import extract_frames
from app.config import FRAME_DIR

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request, error: str = None):
    return templates.TemplateResponse("upload.html", {"request": request, "error": error})

@router.post("/upload/video")
async def upload_video(file: UploadFile = File(...), every_n: int = 5, max_frames: int = None):
    if not file or file.filename == "":
        return RedirectResponse(url="/upload?error=⚠️ 파일을 선택해주세요", status_code=303)

    path = await save_upload_file(file)

    base_name, _ = os.path.splitext(file.filename)
    frame_output = os.path.join(FRAME_DIR, base_name)
    _ = extract_frames(path, frame_output, every_n=every_n, max_frames=max_frames)

    return RedirectResponse(url="/files", status_code=303)
