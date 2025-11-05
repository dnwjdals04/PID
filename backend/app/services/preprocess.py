# preprocess.py
from __future__ import annotations

import os
import glob
from typing import List, Optional, Tuple, Union

import ffmpeg

# ======================================
# 🔹 출력 디렉토리 초기화
# ======================================
def _ensure_clean_dir(path: str, clean: bool) -> None:
    """출력 디렉토리가 존재하지 않으면 생성하고, 필요 시 내부 파일 초기화"""
    os.makedirs(path, exist_ok=True)
    if clean:
        for f in os.listdir(path):
            fp = os.path.join(path, f)
            if os.path.isfile(fp):
                os.remove(fp)

# ======================================
# 🔹 프레임 추출 (영상 → 이미지)
# ======================================
def extract_frames(
    input_video: str,
    output_dir: str = "./frames",
    fps: Optional[float] = None,
    every_n: Optional[int] = None,
    start_time: Optional[Union[int, float, str]] = None,
    duration: Optional[Union[int, float, str]] = None,
    resize: Optional[Tuple[int, int]] = None,
    img_format: str = "jpg",
    quality: Optional[int] = 1,
    clean_output_dir: bool = True,
) -> List[str]:
    """주어진 영상을 ffmpeg를 이용해 프레임 단위로 추출"""

    # FPS와 every_n은 동시에 사용 불가
    if fps is not None and every_n is not None:
        raise ValueError("Use either fps or every_n, not both.")

    # 지원되는 이미지 포맷 확인
    if img_format not in {"jpg", "png", "bmp", "webp"}:
        raise ValueError("img_format must be one of: 'jpg', 'png', 'bmp', 'webp'")

    _ensure_clean_dir(output_dir, clean_output_dir)

    inp = ffmpeg.input(input_video)

    # 필요한 경우 영상 구간을 잘라냄 (start_time, duration)
    if start_time is not None:
        inp = inp.trim(start=start_time).setpts("PTS-STARTPTS")
        if duration is not None:
            inp = inp.trim(duration=duration).setpts("PTS-STARTPTS")
    elif duration is not None:
        inp = ffmpeg.input(input_video, t=duration)

    stream = inp

    # 프레임 샘플링 방식 선택
    if fps is not None:
        stream = stream.filter("fps", fps=fps)
    elif every_n is not None:
        stream = stream.filter("select", f"not(mod(n\\,{every_n}))").filter("setpts", "N/FRAME_RATE/TB")

    # 리사이즈 설정
    if resize is not None:
        w, h = resize
        stream = stream.filter("scale", w, h, flags="lanczos")

    # 출력 패턴 (예: frame_0001.jpg)
    pattern = os.path.join(output_dir, f"frame_%04d.{img_format}")

    # 품질 설정 (qscale:v — 낮을수록 고화질)
    out_kwargs = {}
    if img_format in {"jpg", "webp"} and quality is not None:
        # qscale:v: lower is better
        out_kwargs["qscale:v"] = quality

    # ffmpeg 실행
    (
        ffmpeg
        .output(stream, pattern, **out_kwargs, start_number=1, vsync="vfr")
        .global_args("-hide_banner")
        .global_args("-loglevel", "error")
        .run()
    )

    # 결과 프레임 경로 리스트 반환
    files = sorted(glob.glob(os.path.join(output_dir, f"frame_*.{img_format}")))
    return files


# ======================================
# 🔹 영상 분할 (청크 단위)
# ======================================
def split_video(video_path: str, out_dir: str = "./chunks", segment_time: int = 10):
    """영상을 일정 시간 단위(segment_time초)로 여러 조각으로 분할"""
    os.makedirs(out_dir, exist_ok=True)
    output_pattern = os.path.join(out_dir, "chunk_%03d.mp4")

    (
        ffmpeg
        .input(video_path)
        .output(output_pattern, c="copy", f="segment", segment_time=segment_time, reset_timestamps=1)
        .overwrite_output()
        .run(quiet=True)
    )

    return sorted(
        [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith(".mp4")]
    )
