"use client";
import { useState } from "react";
import { useDropzone } from "react-dropzone";
import axios from "../lib/api";
import ProgressBar from "./ProgressBar";

export default function UploadCard() {
  // ----------------------------
  // 🔹 상태 관리
  // ----------------------------
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("대기 중");

  // ----------------------------
  // 업로드 함수
  // ----------------------------
  const handleUpload = async (files) => {
    if (!files || files.length === 0) return;
    setLoading(true);
    setStatus("파일 업로드 중...");

    try {
      // 1️⃣ 업로드 요청
      const formData = new FormData();
      formData.append("file", files[0]);

      const uploadRes = await axios.post("/upload", formData, {
        onUploadProgress: (e) => {
          const percent = Math.round((e.loaded * 100) / (e.total || 1));
          setProgress(percent);  // 업로드 진행률 업데이트
        },
      });

      const { file_id } = uploadRes.data;
      setStatus("AI 분석을 준비 중입니다...");

      // 2️⃣ AI 분석 요청
      await axios.post(`/analyze/${file_id}`);
      setStatus("AI 분석이 시작되었습니다...");

      // ✅ SSE 진행률 페이지로 이동
      setTimeout(() => {
        window.location.href = `/processing/${file_id}`;
      }, 1000);
    } catch (err) {
      console.error("업로드/분석 중 오류 발생:", err);
      setStatus("❌ 업로드 또는 분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // ----------------------------
  // Dropzone
  // ----------------------------
  const { getRootProps, getInputProps } = useDropzone({
    onDrop: handleUpload,
  });

  // ----------------------------
  // JSX 렌더링
  // ----------------------------
  return (
    <div className="glass-card upload-box">
      <div {...getRootProps()} className="dropzone">
        <input {...getInputProps()} />
        <p>영상 파일을 드래그하거나 클릭하여 업로드하세요</p>
      </div>

      {loading && (
        <div className="progress-area">
          <ProgressBar progress={progress} />
          <p className="status-text">{status}</p>
        </div>
      )}
    </div>
  );
}
