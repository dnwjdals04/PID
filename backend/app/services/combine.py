# combine.py
from __future__ import annotations

import os
import glob
from typing import Optional, List
import ffmpeg

# ======================================
# 🔹 프레임 → 영상 합성
# ======================================
def combine_frames(
    frames_glob: str,
    output_video: str,
    framerate: float = 30.0,
    codec: str = "libx264",
    crf: int = 18,
    preset: str = "medium",
    pix_fmt: str = "yuv420p",
    audio_from: Optional[str] = None,
) -> str:
    """프레임 이미지들을 받아 하나의 영상(mp4)으로 합성"""

    # printf 스타일 패턴('%d')을 사용한 경우
    use_pattern_type = "%d" in frames_glob or "%0" in frames_glob

    if use_pattern_type:
        # printf-style 입력 (예: frame_%04d.jpg)
        img_in = ffmpeg.input(frames_glob, framerate=framerate)
    else:
        # glob 패턴 입력 (예: *.jpg)
        files = sorted(glob.glob(frames_glob))
        if not files:
            raise FileNotFoundError(f"No frames matched: {frames_glob}")
        # ffmpeg concat용 리스트 파일 생성
        list_path = os.path.join(os.path.dirname(files[0]), "_frames.txt")
        with open(list_path, "w") as f:
            for file in files:
                f.write(f"file '{os.path.abspath(file)}'\n")
        img_in = ffmpeg.input(list_path, f="concat", safe=0, r=framerate)

    stream = img_in

    # 오디오가 존재하면 영상과 합침
    if audio_from:
        a_in = ffmpeg.input(audio_from)
        stream = ffmpeg.concat(stream, a_in.audio, v=1, a=1).node()
        v, a = stream
        out = ffmpeg.output(v, a, output_video, vcodec=codec, crf=crf, preset=preset, pix_fmt=pix_fmt)
    # 오디오 없이 영상만 출력
    else:
        out = ffmpeg.output(stream, output_video, vcodec=codec, crf=crf, preset=preset, pix_fmt=pix_fmt)

    # ffmpeg 실행 (로그 최소화)
    (
        out
        .global_args("-hide_banner")
        .global_args("-loglevel", "error")
        .overwrite_output()
        .run()
    )

    return output_video

# ======================================
# 🔹 여러 영상 연결 (Concatenation)
# ======================================
def concat_videos(video_list: List[str], out_path: str) -> str:
    """분할된 여러 영상을 순서대로 하나의 파일로 이어붙임"""
    if not video_list:
        raise ValueError("No videos provided for concatenation")

    # ffmpeg concat용 리스트 파일 작성
    list_file = os.path.join(os.path.dirname(out_path), "_concat_list.txt")
    with open(list_file, "w") as f:
        for v in video_list:
            f.write(f"file '{os.path.abspath(v)}'\n")
    
    # ffmpeg concat 실행
    (
        ffmpeg
        .input(list_file, f="concat", safe=0)
        .output(out_path, c="copy")
        .overwrite_output()
        .run(quiet=True)
    )

    return out_path