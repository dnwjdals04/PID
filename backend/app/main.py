# main.py
import asyncio
import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import routes
from app.services.state import PROCESS_STATUS

# ======================================
# 🔹 FastAPI 애플리케이션 초기화
# ======================================
app = FastAPI(title="AI-VAMOS Backend")

# ======================================
# 🔹 CORS 설정 (Frontend와 통신 허용)
# ======================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================
# 🔹 라우터 등록
# ======================================
app.include_router(routes.router)


# ======================================
# 🧹 파일 정리
# ======================================
async def cleanup_old_results(interval=600, max_age=3600):
    """일정 주기로 오래된 결과 파일 삭제"""
    while True:
        now = time.time()
        for f in os.listdir("./results"):
            if not f.endswith(".mp4"):
                continue
            path = os.path.join("./results", f)
            try:
                created = os.path.getctime(path)
                if now - created > max_age:
                    os.remove(path)
                    print(f"[🧹 오래된 결과 삭제] {f}")
            except Exception as e:
                print(f"[⚠️ 삭제 실패] {f}: {e}")

        # 오래된 상태 정보 제거
        expired = [
            fid for fid, info in PROCESS_STATUS.items()
            if "created_at" in info and now - info["created_at"] > max_age
        ]
        for fid in expired:
            del PROCESS_STATUS[fid]

        await asyncio.sleep(interval)

# ======================================
# 🚀 FastAPI 앱 시작 시 백그라운드 클린업 태스크 실행
# ======================================
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_old_results(interval=600, max_age=3600))