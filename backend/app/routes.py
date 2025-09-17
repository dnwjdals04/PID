import os
import uuid
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from app.services import ai_engine

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

# 🔹 업로드 라우트 추가
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    with open(save_path, "wb") as f:
        f.write(await file.read())

    return {"file_id": file_id, "path": save_path}

# 🔹 분석 라우트
@router.post("/analyze/{file_id}")
async def analyze_file(file_id: str):
    files = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(file_id)]
    if not files:
        return {"error": "File not found"}
    video_path = os.path.join(UPLOAD_DIR, files[0])

    result = ai_engine.analyze(video_path)
    result["image_urls"] = [f"/result_image/{os.path.basename(img)}" for img in result["images"]]
    return {"file_id": file_id, "analysis": result}

# 🔹 결과 이미지 반환 라우트
@router.get("/result_image/{filename}")
async def get_result_image(filename: str):
    path = os.path.join("./results", filename)
    return FileResponse(path)
