# routes.py
import os
import uuid
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from app.services import preprocess, ai_engine

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    with open(save_path, "wb") as f:
        f.write(await file.read())

    return {"file_id": file_id, "path": save_path}

@router.post("/analyze/{file_id}")
async def analyze_file(file_id: str):
    files = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(file_id)]
    if not files:
        return {"error": "File not found"}
    video_path = os.path.join(UPLOAD_DIR, files[0])

    # ✅ 프레임 추출
    frame_files = preprocess.extract_frames(video_path)
    frame_files = [os.path.join("./frames", f) for f in frame_files]

    # ✅ 프레임 기반 분석
    result = ai_engine.analyze(frame_files, file_id)

    # ✅ 이미지 URL 반환
    result["image_urls"] = [
        f"/result_image/{file_id}/{os.path.basename(img)}"
        for img in result["images"]
    ]
    return {"file_id": file_id, "analysis": result}

@router.get("/result_image/{file_id}/{filename}")
async def get_result_image(file_id: str, filename: str):
    path = os.path.join("./results", file_id, filename)
    return FileResponse(path)
