import os
import subprocess

def extract_frames(video_path: str, out_dir="./frames"):
    """
    ffmpeg을 사용해 1초마다 프레임 추출
    """
    os.makedirs(out_dir, exist_ok=True)

    # 기존 프레임 삭제
    for f in os.listdir(out_dir):
        os.remove(os.path.join(out_dir, f))

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", "fps=1", f"{out_dir}/frame_%04d.jpg",
        "-hide_banner", "-loglevel", "error"
    ]
    subprocess.run(cmd)

    return [f for f in os.listdir(out_dir) if f.endswith(".jpg")]
