"""
Preprocessing utilities for video frame extraction using ffmpeg-python.

This module exposes:
- extract_frames(): programmatic API
- CLI usage: `python -m app.services.preprocess --help`
"""
from __future__ import annotations

import os
import glob
from typing import List, Optional, Tuple, Union

import ffmpeg


def _ensure_clean_dir(path: str, clean: bool) -> None:
    os.makedirs(path, exist_ok=True)
    if clean:
        for f in os.listdir(path):
            fp = os.path.join(path, f)
            if os.path.isfile(fp):
                os.remove(fp)


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
    """
    Extract frames from a video using ffmpeg-python.

    Args:
        input_video: path to input video file.
        output_dir: folder to save frames.
        fps: desired frames per second to sample (e.g., 1.0 -> 1 frame/sec).
        every_n: keep every Nth frame (alternative to fps). Use either fps or every_n.
        start_time: trim start, e.g. 3.5 (seconds) or '00:00:03.5'.
        duration: duration to process in seconds or 'HH:MM:SS'.
        resize: (width, height) to scale frames, e.g., (640, 360).
        img_format: one of {'jpg', 'png', 'bmp', 'webp'}.
        quality: encoder quality. For jpg/webp, lower is higher quality (1-31). For png ignored.
        clean_output_dir: whether to delete existing files in output_dir first.

    Returns:
        List of saved frame file paths (sorted).
    """
    if fps is not None and every_n is not None:
        raise ValueError("Use either fps or every_n, not both.")

    if img_format not in {"jpg", "png", "bmp", "webp"}:
        raise ValueError("img_format must be one of: 'jpg', 'png', 'bmp', 'webp'")

    _ensure_clean_dir(output_dir, clean_output_dir)

    # Build ffmpeg stream
    inp = ffmpeg.input(input_video)

    # Optional trim
    if start_time is not None:
        inp = inp.trim(start=start_time).setpts("PTS-STARTPTS")
        if duration is not None:
            inp = inp.trim(duration=duration).setpts("PTS-STARTPTS")
    elif duration is not None:
        # duration without start_time -> use -t on input
        inp = ffmpeg.input(input_video, t=duration)

    stream = inp

    # Sampling
    if fps is not None:
        stream = stream.filter("fps", fps=fps)
    elif every_n is not None:
        # select every Nth frame
        stream = stream.filter("select", f"not(mod(n\\,{every_n}))").filter("setpts", "N/FRAME_RATE/TB")

    # Resize
    if resize is not None:
        w, h = resize
        stream = stream.filter("scale", w, h, flags="lanczos")

    # Output pattern
    pattern = os.path.join(output_dir, f"frame_%04d.{img_format}")

    # Quality flags
    out_kwargs = {}
    if img_format in {"jpg", "webp"} and quality is not None:
        # qscale:v: lower is better
        out_kwargs["qscale:v"] = quality

    (
        ffmpeg
        .output(stream, pattern, **out_kwargs, start_number=1, vsync="vfr")
        .global_args("-hide_banner")
        .global_args("-loglevel", "error")
        .run()
    )

    files = sorted(glob.glob(os.path.join(output_dir, f"frame_*.{img_format}")))
    return files


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract frames from a video using ffmpeg-python.")
    parser.add_argument("input_video", type=str, help="Path to input video")
    parser.add_argument("--output-dir", type=str, default="./frames", help="Where to save frames")
    parser.add_argument("--fps", type=float, default=None, help="Frames per second to extract")
    parser.add_argument("--every-n", type=int, default=None, help="Keep every Nth frame (alternative to --fps)")
    parser.add_argument("--start-time", type=str, default=None, help="Start time (e.g., 3.5 or 00:00:03.5)")
    parser.add_argument("--duration", type=str, default=None, help="Duration to process (e.g., 10 or 00:00:10)")
    parser.add_argument("--resize", type=str, default=None, help="WxH (e.g., 640x360)")
    parser.add_argument("--img-format", type=str, default="jpg", choices=["jpg", "png", "bmp", "webp"], help="Image format")
    parser.add_argument("--quality", type=int, default=None, help="Quality (1-31 for jpg/webp; lower is better)")
    parser.add_argument("--no-clean", action="store_true", help="Do not clean output directory before writing")

    args = parser.parse_args()
    resize_tuple = None
    if args.resize:
        try:
            w, h = args.resize.lower().split("x")
            resize_tuple = (int(w), int(h))
        except Exception:
            raise SystemExit("Invalid --resize. Use WxH, e.g., 640x360")

    files = extract_frames(
        input_video=args.input_video,
        output_dir=args.output_dir,
        fps=args.fps,
        every_n=args.every_n,
        start_time=args.start_time,
        duration=args.duration,
        resize=resize_tuple,
        img_format=args.img_format,
        quality=args.quality,
        clean_output_dir=not args.no_clean,
    )
    print(f"Saved {len(files)} frames to {args.output_dir}")


def split_video(video_path: str, out_dir: str = "./chunks", segment_time: int = 10):
    """
    주어진 영상을 일정 구간(segment_time초) 단위로 분할합니다.
    Returns:
        List[str]: 분할된 영상 조각 파일 경로 리스트
    """
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