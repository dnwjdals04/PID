#media_utils.py
import cv2
import os

def extract_frames(video_path: str, output_dir: str, every_n: int = 1, max_frames: int = None):
    """
    비디오를 프레임 단위로 추출.
    - every_n: n프레임마다 저장
    - max_frames: 최대 저장 프레임 수 (None이면 제한 없음)
    """
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    frame_count = 0
    saved_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % every_n == 0:
            filename = os.path.join(output_dir, f"frame_{frame_count:06d}.jpg")
            cv2.imwrite(filename, frame)
            saved_count += 1

        frame_count += 1
        if max_frames and saved_count >= max_frames:
            break

    cap.release()
    return {"frames_extracted": saved_count, "output_dir": output_dir}
