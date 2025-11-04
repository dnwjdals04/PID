"""
Utilities to combine image frames back into a video using ffmpeg-python.

Exposes:
- combine_frames(): programmatic API
- CLI usage: `python -m app.services.combine --help`
"""
from __future__ import annotations

import os
import glob
from typing import Optional, List
import ffmpeg


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
    """
    Combine image frames to a video using ffmpeg-python.

    Args:
        frames_glob: glob/printf-style pattern to frames, e.g., './frames/frame_%06d.jpg'
                      (Use printf-style when possible; glob like './frames/*.jpg' also works.)
        output_video: path to write the video, e.g., './output.mp4'
        framerate: frames per second of the output video.
        codec: video codec (e.g., libx264, libx265, libvpx-vp9).
        crf: quality for CRF-based codecs (lower is better; 18 visually lossless for x264).
        preset: encoder speed/quality tradeoff (ultrafast...placebo) for x264/x265.
        pix_fmt: pixel format, 'yuv420p' for broad compatibility.
        audio_from: optional path to a media file to borrow audio track from.

    Returns:
        Path to the created video.
    """
    # If user provided a "%d" style pattern, use that with input options.
    use_pattern_type = "%d" in frames_glob or "%0" in frames_glob

    if use_pattern_type:
        img_in = ffmpeg.input(frames_glob, framerate=framerate)
    else:
        # If it's a wildcard glob, expand and feed as concat filter
        files = sorted(glob.glob(frames_glob))
        if not files:
            raise FileNotFoundError(f"No frames matched: {frames_glob}")
        # Build a file list for concat demuxer
        list_path = os.path.join(os.path.dirname(files[0]), "_frames.txt")
        with open(list_path, "w") as f:
            for file in files:
                f.write(f"file '{os.path.abspath(file)}'\n")
        img_in = ffmpeg.input(list_path, f="concat", safe=0, r=framerate)

    stream = img_in

    # Map audio if provided
    if audio_from:
        a_in = ffmpeg.input(audio_from)
        stream = ffmpeg.concat(stream, a_in.audio, v=1, a=1).node()
        v, a = stream
        out = ffmpeg.output(v, a, output_video, vcodec=codec, crf=crf, preset=preset, pix_fmt=pix_fmt)
    else:
        out = ffmpeg.output(stream, output_video, vcodec=codec, crf=crf, preset=preset, pix_fmt=pix_fmt)

    (
        out
        .global_args("-hide_banner")
        .global_args("-loglevel", "error")
        .overwrite_output()
        .run()
    )

    return output_video


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Combine frames back into a video using ffmpeg-python.")
    parser.add_argument("frames_pattern", type=str, help="Pattern to frames, e.g., ./frames/frame_%06d.jpg or ./frames/*.png")
    parser.add_argument("-o", "--output", type=str, default="./output.mp4", help="Output video path")
    parser.add_argument("--fps", type=float, default=30.0, help="Output framerate")
    parser.add_argument("--codec", type=str, default="libx264", help="Video codec (libx264, libx265, libvpx-vp9, etc.)")
    parser.add_argument("--crf", type=int, default=18, help="CRF quality (lower is better)")
    parser.add_argument("--preset", type=str, default="medium", help="Encoder preset")
    parser.add_argument("--pix-fmt", type=str, default="yuv420p", help="Pixel format")
    parser.add_argument("--audio-from", type=str, default=None, help="Optional media path to source audio from")

    args = parser.parse_args()

    out_path = combine_frames(
        frames_glob=args.frames_pattern,
        output_video=args.output,
        framerate=args.fps,
        codec=args.codec,
        crf=args.crf,
        preset=args.preset,
        pix_fmt=args.pix_fmt,
        audio_from=args.audio_from,
    )
    print(f"Created video: {out_path}")


def concat_videos(video_list: List[str], out_path: str) -> str:
    """
    여러 개의 비디오 파일을 하나로 이어붙입니다.
    Args:
        video_list: 영상 파일 경로 리스트 (순서 중요)
        out_path: 결과 저장 경로
    Returns:
        out_path (str)
    """
    if not video_list:
        raise ValueError("No videos provided for concatenation")

    # ffmpeg concat용 리스트 파일 생성
    list_file = os.path.join(os.path.dirname(out_path), "_concat_list.txt")
    with open(list_file, "w") as f:
        for v in video_list:
            f.write(f"file '{os.path.abspath(v)}'\n")

    (
        ffmpeg
        .input(list_file, f="concat", safe=0)
        .output(out_path, c="copy")
        .overwrite_output()
        .run(quiet=True)
    )

    return out_path