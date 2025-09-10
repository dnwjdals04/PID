import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import UPLOAD_DIR, FRAME_DIR

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/files", response_class=HTMLResponse)
async def list_files(request: Request):
    items = []
    for name in os.listdir(UPLOAD_DIR):
        p = os.path.join(UPLOAD_DIR, name)
        if os.path.isfile(p):
            size = os.path.getsize(p)
            base_name, _ = os.path.splitext(name)
            frame_dir = os.path.join(FRAME_DIR, base_name)
            thumbnail_url = None

            if os.path.exists(frame_dir) and os.path.isdir(frame_dir):
                frames = sorted(os.listdir(frame_dir))
                if frames:
                    thumbnail_url = f"/frames/{base_name}/{frames[0]}"

            items.append({"name": name, "size": size, "thumbnail_url": thumbnail_url})

    return templates.TemplateResponse("files.html", {"request": request, "items": items})
