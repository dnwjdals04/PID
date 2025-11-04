import os
import uuid
import asyncio
import mimetypes
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from app.services import preprocess, ai_engine, combine
from app.services.state import PROCESS_STATUS, PROCESS_LOCK

router = APIRouter()

UPLOAD_DIR = "./uploads"
RESULT_DIR = "./results"
CHUNK_DIR = "./chunks"
FRAME_DIR = "./frames"


os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(CHUNK_DIR, exist_ok=True)
os.makedirs(FRAME_DIR, exist_ok=True)


# ==========================================
# ✅ Chunk 처리 함수 (Thread-safe)
# ==========================================
def process_chunk_with_progress(chunk_path, idx, total_chunks, file_id):
    """프레임 추출 → 마스킹 (Thread 환경)"""
    frame_dir = os.path.join(FRAME_DIR, f"{file_id}_{idx}")
    os.makedirs(frame_dir, exist_ok=True)

    frames = preprocess.extract_frames(chunk_path, frame_dir, fps=30.0, img_format="jpg")
    frame_paths = [os.path.join(frame_dir, os.path.basename(f)) for f in frames]

    ai_engine.analyze(frame_paths, file_id=file_id, chunk_idx=idx, total_chunks=total_chunks)
    with PROCESS_LOCK:
        PROCESS_STATUS[file_id]["chunks"][idx] = 100
    return idx


# ==========================================
# ✅ 업로드
# ==========================================
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    with open(save_path, "wb") as f:
        f.write(await file.read())
    return {"file_id": file_id, "path": save_path}


# ==========================================
# ✅ AI 분석 시작 (Thread 기반 병렬)
# ==========================================
@router.post("/analyze/{file_id}")
async def analyze_file(file_id: str):
    files = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(file_id)]
    if not files:
        raise HTTPException(status_code=404, detail="File not found")

    video_path = os.path.join(UPLOAD_DIR, files[0])
    PROCESS_STATUS[file_id] = {
        "progress": 0,
        "stage": "AI 분석 준비 중...",
        "status": "processing",
        "chunks": [],
    }

    async def run_analysis():
        try:
            PROCESS_STATUS[file_id]["stage"] = "splitting"
            PROCESS_STATUS[file_id]["progress"] = 5

            chunk_dir = os.path.join(CHUNK_DIR, file_id)
            chunks = preprocess.split_video(video_path, out_dir=chunk_dir, segment_time=10)
            total_chunks = len(chunks)
            PROCESS_STATUS[file_id]["chunks"] = [0] * total_chunks
            PROCESS_STATUS[file_id]["progress"] = 10
            PROCESS_STATUS[file_id]["stage"] = "masking"

            # ✅ Thread 기반 병렬 처리
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=min(os.cpu_count() or 1, total_chunks)) as executor:
                tasks = [
                    loop.run_in_executor(
                        executor, 
                        process_chunk_with_progress, 
                        chunk, 
                        i, 
                        total_chunks, 
                        file_id
                    )
                    for i, chunk in enumerate(chunks)
                ]
                await asyncio.gather(*tasks)

            # ✅ 청크별 영상 결합
            PROCESS_STATUS[file_id]["stage"] = "combining_chunks"
            PROCESS_STATUS[file_id]["progress"] = 90
            chunk_videos = []
            for i in range(total_chunks):
                chunk_dir_result = os.path.join(RESULT_DIR, f"{file_id}_{i}")
                chunk_video_path = os.path.join(RESULT_DIR, f"{file_id}_chunk_{i}.mp4")
                combine.combine_frames(
                    frames_glob=f"{chunk_dir_result}/processed_frame_%04d.jpg",
                    output_video=chunk_video_path,
                    framerate=30.0,
                )
                chunk_videos.append(chunk_video_path)

            # ✅ 최종 연결
            PROCESS_STATUS[file_id]["stage"] = "combining_final"
            PROCESS_STATUS[file_id]["progress"] = 95

            final_output = os.path.join(RESULT_DIR, f"{file_id}_final.mp4")
            combine.concat_videos(chunk_videos, out_path=final_output)

            PROCESS_STATUS[file_id]["progress"] = 100
            PROCESS_STATUS[file_id]["stage"] = "done"
            PROCESS_STATUS[file_id]["status"] = "done"

        except Exception as e:
            PROCESS_STATUS[file_id]["status"] = "error"
            PROCESS_STATUS[file_id]["error"] = str(e)
            print(f"[❌ 분석 실패] {e}")

    asyncio.create_task(run_analysis())
    return {"status": "processing", "file_id": file_id}


# ==========================================
# ✅ SSE 진행률 스트림
# ==========================================
@router.get("/progress-stream/{file_id}")
async def progress_stream(request: Request, file_id: str):
    async def event_generator():
        last_progress = -1.0
        while True:
            if await request.is_disconnected():
                print(f"❌ SSE disconnected: {file_id}")
                break

            info = PROCESS_STATUS.get(file_id)
            if not info:
                await asyncio.sleep(0.5)
                continue

            progress = float(info["progress"])
            stage = info["stage"]
            status = info["status"]

            if abs(progress - last_progress) >= 0.1:
                yield f"data: {progress},{stage},{status}\n\n"
                last_progress = progress

            if status in ["done", "error"]:
                break

            await asyncio.sleep(0.3)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# -------------------------------
# 결과 영상 조회
# -------------------------------
@router.get("/result_video/{filename}")
async def get_result_video(filename: str):
    path = os.path.join(RESULT_DIR, filename)
    if not os.path.exists(path):
        return {"error": "Video not found"}
    mime_type, _ = mimetypes.guess_type(path)
    return FileResponse(path, media_type=mime_type or "application/octet-stream")


# -------------------------------
# 결과 데이터 조회
# -------------------------------
@router.get("/result/{file_id}")
async def get_result(file_id: str):
    final_video_path = os.path.join(RESULT_DIR, f"{file_id}_final.mp4")
    if not os.path.exists(final_video_path):
        raise HTTPException(status_code=404, detail="Result not found")

    fake_detections = [
        {"type": "face", "count": 12, "start": 0, "duration": 5},
        {"type": "plate", "count": 3, "start": 6, "duration": 2},
    ]

    return {
        "original_url": f"/uploads/{file_id}.mp4",
        "masked_url": f"/result_video/{file_id}_final.mp4",
        "detections": fake_detections,
    }
