# ai_engine.py
import os
import cv2
from ultralytics import YOLO
from paddleocr import PaddleOCR

face_model = YOLO("yolov8n-face.pt")
plate_model = YOLO("yolov8n.pt")
ocr = PaddleOCR(use_angle_cls=True, lang='korean')

RESULT_DIR = "./results"
os.makedirs(RESULT_DIR, exist_ok=True)

def analyze(frame_files: list[str], file_id: str):
    frame_results = []
    saved_images = []
    
    result_dir = os.path.join(RESULT_DIR, file_id)
    os.makedirs(result_dir, exist_ok=True)

    for f in os.listdir(result_dir):
        os.remove(os.path.join(result_dir, f))

    for frame_id, frame_path in enumerate(frame_files, start=1):
        frame = cv2.imread(frame_path)
        detections = []

        # 얼굴 탐지
        for pred in face_model.predict(frame, verbose=False)[0].boxes:
            x1, y1, x2, y2 = map(int, pred.xyxy[0])
            conf = float(pred.conf[0])
            detections.append({
                "type": "face",
                "bbox": [x1, y1, x2-x1, y2-y1],
                "confidence": round(conf, 2)
            })
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # 객체 탐지
        for pred in plate_model.predict(frame, verbose=False)[0].boxes:
            x1, y1, x2, y2 = map(int, pred.xyxy[0])
            conf = float(pred.conf[0])
            detections.append({
                "type": "object",
                "bbox": [x1, y1, x2-x1, y2-y1],
                "confidence": round(conf, 2)
            })
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

        # OCR
        ocr_results = ocr.ocr(frame_path)
        if ocr_results:
            for line in ocr_results[0]:
                try:
                    bbox, (text, conf) = line
                    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = bbox
                    detections.append({
                        "type": "text",
                        "bbox": [int(x1), int(y1), int(x3 - x1), int(y3 - y1)],
                        "content": text,
                        "confidence": round(float(conf), 2)
                    })
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x3), int(y3)), (0, 0, 255), 2)
                except Exception as e:
                    print(f"[OCR Parse Error] {e}, line={line}")

        # 결과 저장
        out_path = os.path.join(result_dir, f"result_{frame_id:04d}.jpg")
        cv2.imwrite(out_path, frame)
        saved_images.append(out_path)

        frame_results.append({
            "frame": os.path.basename(frame_path),
            "detections": detections
        })
        
    return {"frames": frame_results, "images": saved_images}
