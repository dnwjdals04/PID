import os
import cv2
from ultralytics import YOLO
from paddleocr import PaddleOCR

# 모델 로드
face_model = YOLO("yolov8n-face.pt")
plate_model = YOLO("yolov8n.pt")
ocr = PaddleOCR(use_angle_cls=True, lang='korean')

RESULT_DIR = "./results"
os.makedirs(RESULT_DIR, exist_ok=True)

def analyze(video_path: str):
    cap = cv2.VideoCapture(video_path)
    frame_results = []
    frame_id = 0
    saved_images = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_id += 1
        detections = []

        # 얼굴 탐지
        for pred in face_model.predict(frame, verbose=False)[0].boxes:
            x1, y1, x2, y2 = map(int, pred.xyxy[0])
            conf = float(pred.conf[0])
            detections.append({"type": "face", "bbox": [x1, y1, x2-x1, y2-y1], "confidence": round(conf, 2)})
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # 객체 탐지
        for pred in plate_model.predict(frame, verbose=False)[0].boxes:
            x1, y1, x2, y2 = map(int, pred.xyxy[0])
            conf = float(pred.conf[0])
            detections.append({"type": "object", "bbox": [x1, y1, x2-x1, y2-y1], "confidence": round(conf, 2)})
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

        # OCR
        tmp_path = f"./frames/tmp_{frame_id}.jpg"
        os.makedirs("./frames", exist_ok=True)
        cv2.imwrite(tmp_path, frame)

        ocr_results = ocr.ocr(tmp_path)  # PaddleOCR 3.x는 cls 인자 필요 없음
        if ocr_results:
            for line in ocr_results[0]:
                try:
                    bbox, (text, conf) = line   # bbox: 꼭짓점 4개 좌표
                    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = bbox

                    detections.append({
                        "type": "text",
                        "bbox": [int(x1), int(y1), int(x3 - x1), int(y3 - y1)],
                        "content": text,
                        "confidence": round(float(conf), 2)
                    })

                    # 빨간색 박스 그리기
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x3), int(y3)), (0, 0, 255), 2)

                except Exception as e:
                    print(f"[OCR Parse Error] {e}, line={line}")

        os.remove(tmp_path)

        # 결과 이미지 저장 (앞 3프레임만)
        if frame_id <= 3:
            out_path = os.path.join(RESULT_DIR, f"result_{frame_id:04d}.jpg")
            cv2.imwrite(out_path, frame)
            saved_images.append(out_path)

        frame_results.append({"frame": f"frame_{frame_id:04d}.jpg", "detections": detections})

        if frame_id >= 3:  # 빠른 데모용: 앞 3프레임만
            break

    cap.release()

    return {"frames": frame_results, "images": saved_images}
