# state.py
from threading import Lock

# ======================================
# 🔹 전역 상태 관리 객체
# ======================================
# 각 파일 ID(file_id)별 진행 상태를 저장하는 딕셔너리
# 예시:
# PROCESS_STATUS[file_id] = {
#     "progress": 73.4,              # 전체 진행률 (%)
#     "stage": "masking",            # 현재 단계
#     "status": "processing",        # 상태 ("processing" / "done" / "error")
#     "chunks": [0, 100, 85, ...],   # 청크별 진행률 리스트
# }
PROCESS_STATUS = {}

# 멀티스레드 환경에서 진행률 갱신 시 동기화용 락
PROCESS_LOCK = Lock()
