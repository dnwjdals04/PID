"use client";
import { useEffect, useState } from "react";
import VideoViewer from "../../../components/VideoViewer";

export default function ResultPage({ params }) {
  const { id } = params;
  const [masked_url, setMaskedUrl] = useState("");

  useEffect(() => {
    // ✅ FastAPI에서 제공하는 결과 영상 URL 지정
    setMaskedUrl(`http://localhost:8000/result_video/${id}_final.mp4`);
  }, [id]);

  if (!masked_url) return <p>로딩 중...</p>;

  return (
    <div className="page-wrapper">
      <h2>결과 보기</h2>
      <VideoViewer masked={masked_url} />
    </div>
  );
}
