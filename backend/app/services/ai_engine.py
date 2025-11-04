import os
import cv2
import numpy as np
import logging
from ultralytics import YOLO
from insightface.app import FaceAnalysis

# ======================================
# 🔹 로깅 설정
# ======================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ======================================
# 🔹 전역 변수 및 설정
# ======================================
model = None
face_app = None

BLUR_MODE = 'mosaic'      # 'gaussian', 'box', 'bilateral', 'mosaic'
FEATHER_PX = 6            # 경계 부드럽게 처리
FACE_PAD_RATIO = 0.18     # 얼굴 영역 확장 비율
FALLBACK_TO_PERSON_MASK = True  # 얼굴 미검출 시 전신 블러 폴백


# ======================================
# 🔹 모델 로드
# ======================================
def load_model():
    global model, face_app

    if model is not None and face_app is not None:
        logger.info("✅ 모델들이 이미 로드되어 있습니다.")
        return True

    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        MODEL_PATH = os.path.join(BASE_DIR, "models", "best.pt")

        if not os.path.exists(MODEL_PATH):
            logger.error(f"❌ 모델 파일 없음: {MODEL_PATH}")
            return False

        model = YOLO(MODEL_PATH, task="segment")
        logger.info(f"✅ YOLO 모델 로드 성공: {MODEL_PATH}")
        logger.info(f"클래스 이름: {model.names}")

        # 얼굴 검출 모델 로드
        face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        face_app.prepare(ctx_id=0, det_size=(640, 640))
        logger.info("✅ 얼굴 검출 모델 로드 성공")

        return True

    except Exception as e:
        logger.error(f"❌ 모델 로드 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


# ======================================
# 🔹 유틸 함수
# ======================================
def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def expand_box(x1, y1, x2, y2, pad_ratio, W, H):
    w = x2 - x1
    h = y2 - y1
    px = int(round(w * pad_ratio))
    py = int(round(h * pad_ratio))
    ex1 = clamp(x1 - px, 0, W - 1)
    ey1 = clamp(y1 - py, 0, H - 1)
    ex2 = clamp(x2 + px, 0, W - 1)
    ey2 = clamp(y2 + py, 0, H - 1)
    return ex1, ey1, ex2, ey2

def adaptive_kernel(w, h, frac=0.15, kmin=9, kmax=91):
    k = int(round(min(w, h) * frac))
    if k % 2 == 0:
        k += 1
    return clamp(k, kmin, kmax)

def build_alpha_from_mask(mask_uint8, feather_px=6):
    if feather_px <= 0:
        return (mask_uint8 / 255.0).astype(np.float32)

    dist = cv2.distanceTransform(255 - mask_uint8, cv2.DIST_L2, 3)
    edge = np.clip(dist / float(feather_px), 0, 1)
    alpha = (mask_uint8 / 255.0) * (1 - edge)
    return np.clip(alpha, 0, 1).astype(np.float32)


# ======================================
# 🔹 블러 함수
# ======================================
def apply_blur_with_alpha(img, mask_uint8, blur_mode='mosaic', feather_px=6, bbox_hint=None):
    H, W = img.shape[:2]
    alpha = build_alpha_from_mask(mask_uint8, feather_px)
    alpha3 = alpha[..., None]

    # 커널 크기
    if bbox_hint:
        x1, y1, x2, y2 = bbox_hint
        k = adaptive_kernel(x2 - x1, y2 - y1, 0.15)
    else:
        k = 25
        if k % 2 == 0:
            k += 1

    # 블러 방식
    if blur_mode == 'gaussian':
        blurred = cv2.GaussianBlur(img, (k, k), 0)
    elif blur_mode == 'box':
        blurred = cv2.blur(img, (k, k))
    elif blur_mode == 'bilateral':
        blurred = cv2.bilateralFilter(img, 9, 75, 75)
    elif blur_mode == 'mosaic':
        cell = max(8, int(round(k * 0.6)))
        small = cv2.resize(img, (max(1, W // cell), max(1, H // cell)), interpolation=cv2.INTER_LINEAR)
        blurred = cv2.resize(small, (W, H), interpolation=cv2.INTER_NEAREST)
    else:
        blurred = img.copy()

    out = (alpha3 * blurred + (1 - alpha3) * img).astype(np.uint8)
    return out


def mask_from_polygon_or_bbox(mask_shape, bbox=None, ellipse=False):
    mask = np.zeros(mask_shape[:2], dtype=np.uint8)
    if bbox is not None:
        x1, y1, x2, y2 = map(int, bbox)
        if ellipse:
            cx = (x1 + x2)//2
            cy = (y1 + y2)//2
            ax = (x2 - x1)//2
            ay = (y2 - y1)//2
            cv2.ellipse(mask, (cx, cy), (ax, ay), 0, 0, 360, 255, -1)
        else:
            cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
    return mask


# ======================================
# 🔹 사람 및 차량 처리
# ======================================
def process_person_with_face_detection(img, out, x1, y1, x2, y2, masks, i, blur_mode):
    global face_app
    H, W = out.shape[:2]
    rx1, ry1, rx2, ry2 = expand_box(x1, y1, x2, y2, pad_ratio=0.02, W=W, H=H)
    roi = out[ry1:ry2, rx1:rx2]

    try:
        faces = face_app.get(roi)
    except Exception as e:
        logger.warning(f"얼굴 검출 실패: {e}")
        faces = []

    face_found = False
    for f in faces:
        fx1, fy1, fx2, fy2 = f.bbox.astype(int)
        fx1, fy1, fx2, fy2 = fx1 + rx1, fy1 + ry1, fx2 + rx1, fy2 + ry1
        fx1, fy1, fx2, fy2 = expand_box(fx1, fy1, fx2, fy2, FACE_PAD_RATIO, W, H)
        face_mask = mask_from_polygon_or_bbox(out.shape, bbox=(fx1, fy1, fx2, fy2), ellipse=True)
        out = apply_blur_with_alpha(out, face_mask, blur_mode=blur_mode, feather_px=FEATHER_PX, bbox_hint=(fx1, fy1, fx2, fy2))
        face_found = True
        logger.info(f"[FACE] 얼굴 블러 적용: ({fx1}, {fy1}, {fx2}, {fy2})")

    if not face_found and FALLBACK_TO_PERSON_MASK:
        logger.info("[FACE] 얼굴 없음 → 전신 블러 폴백 적용")
        if masks is not None:
            m = (masks[i] * 255).astype(np.uint8)
            m = cv2.resize(m, (W, H), interpolation=cv2.INTER_NEAREST)
        else:
            m = mask_from_polygon_or_bbox(out.shape, bbox=(x1, y1, x2, y2))
        out = apply_blur_with_alpha(out, m, blur_mode=blur_mode, feather_px=FEATHER_PX, bbox_hint=(x1, y1, x2, y2))
        logger.info("[FACE] 전신 블러 폴백 완료")

    return out


def process_vehicle(out, x1, y1, x2, y2, masks, i, blur_mode):
    H, W = out.shape[:2]
    if masks is not None:
        m = (masks[i] * 255).astype(np.uint8)
        m = cv2.resize(m, (W, H), interpolation=cv2.INTER_NEAREST)
    else:
        m = mask_from_polygon_or_bbox(out.shape, bbox=(x1, y1, x2, y2))
    out = apply_blur_with_alpha(out, m, blur_mode=blur_mode, feather_px=FEATHER_PX, bbox_hint=(x1, y1, x2, y2))
    logger.info(f"[VEHICLE] 블러 적용: ({x1}, {y1}, {x2}, {y2})")
    return out


# ======================================
# 🔹 이미지 처리 (핵심 수정됨)
# ======================================
def process_image_advanced(image_input, blur_mode=BLUR_MODE):
    global model, face_app

    if model is None or face_app is None:
        logger.error("모델이 로드되지 않았습니다.")
        return None

    if isinstance(image_input, str):
        img = cv2.imread(image_input)
        if img is None:
            logger.error(f"이미지를 읽을 수 없습니다: {image_input}")
            return None
    elif isinstance(image_input, np.ndarray):
        img = image_input
    else:
        logger.error("잘못된 이미지 입력 타입입니다.")
        return None

    results = model(img, verbose=False)[0]
    out = img.copy()

    masks = results.masks.data.cpu().numpy() if results.masks is not None else None
    boxes = results.boxes

    if boxes is None or len(boxes) == 0:
        logger.info("탐지된 객체가 없습니다.")
        return out

    cls_ids = boxes.cls.cpu().numpy().astype(int)
    logger.info(f"감지된 클래스 목록: {cls_ids}")

    for i, cls_id in enumerate(cls_ids):
        x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy().astype(int)
        confidence = float(boxes.conf[i].cpu().numpy())

        logger.info(f"[YOLO] 객체 {i}: 클래스={cls_id}, 신뢰도={confidence:.2f}, 좌표=({x1},{y1},{x2},{y2})")

        if confidence < 0.3:
            continue

        # 🔸 현재 모델은 0=person, 1=vehicle 구조
        if cls_id == 0:
            out = process_person_with_face_detection(img, out, x1, y1, x2, y2, masks, i, blur_mode)
        elif cls_id == 1:
            out = process_vehicle(out, x1, y1, x2, y2, masks, i, blur_mode)

    return out


# ======================================
# 🔹 analyze (FastAPI용) — SSE 실시간 업데이트 개선 버전
# ======================================
from app.services.state import PROCESS_STATUS, PROCESS_LOCK

def analyze(frame_files, file_id, chunk_idx=None, total_chunks=None, blur_mode=BLUR_MODE):
    """각 프레임 단위 및 내부 객체 처리 단위로 진행률을 갱신하는 개선된 analyze 함수"""
    from time import time

    if model is None or face_app is None:
        logger.error("모델이 로드되지 않았습니다.")
        return {"error": "모델이 로드되지 않았습니다.", "images": [], "total_detections": 0}

    result_dir = os.path.join("./results", f"{file_id}_{chunk_idx or 0}")
    os.makedirs(result_dir, exist_ok=True)

    total_frames = len(frame_files)
    processed_images = []
    total_detections = 0

    start_time = time()
    logger.info(f"[분석 시작] file_id={file_id}, chunk={chunk_idx}, 총 {total_frames} 프레임")

    for i, frame_path in enumerate(frame_files):
        if not os.path.exists(frame_path):
            logger.warning(f"⚠️ 프레임 없음: {frame_path}")
            continue

        img = cv2.imread(frame_path)
        if img is None:
            continue

        # YOLO 탐지
        results = model(img, verbose=False)[0]
        out = img.copy()
        masks = results.masks.data.cpu().numpy() if results.masks is not None else None
        boxes = results.boxes

        # 객체 탐지 없는 경우
        if boxes is None or len(boxes) == 0:
            cv2.imwrite(os.path.join(result_dir, f"processed_frame_{i:04d}.jpg"), out)
            continue

        cls_ids = boxes.cls.cpu().numpy().astype(int)
        for j, cls_id in enumerate(cls_ids):
            x1, y1, x2, y2 = boxes.xyxy[j].cpu().numpy().astype(int)
            conf = float(boxes.conf[j].cpu().numpy())
            if conf < 0.3:
                continue

            # --- 객체별 분기 ---
            if cls_id == 0:
                out = process_person_with_face_detection(img, out, x1, y1, x2, y2, masks, j, blur_mode)
            elif cls_id == 1:
                out = process_vehicle(out, x1, y1, x2, y2, masks, j, blur_mode)

            total_detections += 1

            # 🔸 (1) 객체별 부분 진행률 업데이트 (더 부드러운 SSE 표시용)
            if file_id in PROCESS_STATUS and chunk_idx is not None and total_chunks is not None:
                with PROCESS_LOCK:
                    # 한 프레임 내 객체 비율 반영 (예: 0.1%)
                    partial = ((i + j / len(cls_ids)) / total_frames) * 100
                    PROCESS_STATUS[file_id]["chunks"][chunk_idx] = partial
                    avg = sum(PROCESS_STATUS[file_id]["chunks"]) / total_chunks
                    PROCESS_STATUS[file_id]["progress"] = round(10 + avg * 0.85, 2)
                    PROCESS_STATUS[file_id]["stage"] = (
                        f"청크 {chunk_idx+1}/{total_chunks} - 프레임 {i+1}/{total_frames}"
                    )

        # --- 프레임 저장 ---
        output_path = os.path.join(result_dir, f"processed_frame_{i:04d}.jpg")
        cv2.imwrite(output_path, out)
        processed_images.append(output_path)

        # 🔸 (2) 프레임 단위 진행률 업데이트
        if file_id in PROCESS_STATUS and chunk_idx is not None and total_chunks is not None:
            local_progress = ((i + 1) / total_frames) * 100
            with PROCESS_LOCK:
                PROCESS_STATUS[file_id]["chunks"][chunk_idx] = local_progress
                avg_progress = sum(PROCESS_STATUS[file_id]["chunks"]) / total_chunks
                PROCESS_STATUS[file_id]["progress"] = round(10 + avg_progress * 0.85, 2)
                PROCESS_STATUS[file_id]["stage"] = (
                    f"청크 {chunk_idx+1}/{total_chunks} - 프레임 {i+1}/{total_frames}"
                )
                logger.info(f"[진행률] {file_id}: {PROCESS_STATUS[file_id]['progress']}%")

    elapsed = round(time() - start_time, 2)
    logger.info(f"[✅ 완료] file_id={file_id}, chunk={chunk_idx}, {total_detections}개 탐지, {elapsed}s 소요")

    return {
        "status": "success",
        "images": processed_images,
        "total_detections": total_detections
    }


# ======================================
# 🔹 모델 자동 로드
# ======================================
load_model()
