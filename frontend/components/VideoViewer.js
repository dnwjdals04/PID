"use client";
import { useRef } from "react";

export default function VideoViewer({ masked }) {
  const Ref = useRef(null);

  const sync = (action) => {
    if (action === "play") {
      Ref.current?.play();
    } else {
      Ref.current?.pause();
    }
  };

  return (
    <div className="container">
      <div className="video-box">
        <video ref={Ref} src={masked} controls />
      </div>
      <div className="button-row">
        <button onClick={() => sync("play")} className="button-green">
          재생
        </button>
        <button onClick={() => sync("pause")} className="button-red">
          일시정지
        </button>
      </div>
    </div>
  );
}
