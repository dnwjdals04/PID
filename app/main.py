from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import UPLOAD_DIR, FRAME_DIR
from app.routes.upload import router as upload_router
from app.routes.file_list import router as file_list_router
from app.routes.delete import router as delete_router
from app.routes.play import router as play_router

app = FastAPI(title="AI_VAMOS!")

# 정적 파일 mount
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/frames", StaticFiles(directory=FRAME_DIR), name="frames")

# 템플릿 등록
templates = Jinja2Templates(directory="app/templates")

# 라우터 등록
app.include_router(upload_router)
app.include_router(file_list_router)
app.include_router(delete_router)
app.include_router(play_router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
