# config.py
import os

# 업로드/프레임 디렉토리
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
FRAME_DIR = os.environ.get("FRAME_DIR", "frames")

# 허용 MIME/확장자
ALLOWED_MIME = {"video/mp4", "video/quicktime", "video/x-matroska", "video/x-msvideo"}
ALLOWED_EXT = {".mp4", ".mov", ".mkv", ".avi"}

# 파일 크기 제한
MAX_BYTES = 1_000_000_000  # 1GB

# 디렉토리 생성 보장
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FRAME_DIR, exist_ok=True)
