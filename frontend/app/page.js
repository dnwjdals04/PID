"use client";
import { useState } from "react";

export default function Home() {
  const [file, setFile] = useState(null);
  const [images, setImages] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    setError(null);
    setImages([]);
    setLoading(true);

    if (!file) {
      setError("파일을 선택해주세요.");
      setLoading(false);
      return;
    }

    try {
      // 1. 업로드
      const formData = new FormData();
      formData.append("file", file);

      const uploadRes = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      const uploadData = await uploadRes.json();
      console.log("uploadData:", uploadData);

      if (!uploadData.file_id) {
        setError("업로드 실패: file_id 없음");
        setLoading(false);
        return;
      }

      // 2. 분석
      const analyzeRes = await fetch(
        `http://localhost:8000/analyze/${uploadData.file_id}`,
        { method: "POST" }
      );
      const analyzeData = await analyzeRes.json();
      console.log("analyzeData:", analyzeData);

      if (analyzeData.error) {
        setError(analyzeData.error);
      } else {
        setImages(analyzeData.analysis.image_urls || []);
      }
    } catch (err) {
      setError("서버 요청 실패: " + err.message);
    }

    setLoading(false);
  };

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        padding: 20,
        background: "#f4f6f8",
        fontFamily: "sans-serif",
      }}
    >
      <div
        style={{
          background: "white",
          padding: 30,
          borderRadius: 12,
          boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
          width: "100%",
          maxWidth: 600,
          textAlign: "center",
        }}
      >
        <h1 style={{ fontSize: 24, fontWeight: "bold", marginBottom: 20 }}>
          AI-VAMOS Demo
        </h1>

        <input
          type="file"
          accept="video/*"
          onChange={(e) => setFile(e.target.files[0])}
          style={{
            marginBottom: 15,
            padding: 8,
            border: "1px solid #ccc",
            borderRadius: 6,
            width: "100%",
          }}
        />

        <button
          onClick={handleUpload}
          disabled={loading}
          style={{
            padding: "10px 20px",
            background: loading ? "#94a3b8" : "#2563eb",
            color: "white",
            border: "none",
            borderRadius: 6,
            cursor: "pointer",
            fontSize: 16,
          }}
        >
          {loading ? "분석 중..." : "업로드 & 분석"}
        </button>

        {error && (
          <div style={{ marginTop: 20, color: "red" }}>
            <strong>에러:</strong> {error}
          </div>
        )}
      </div>

      {images.length > 0 && (
        <div
          style={{
            marginTop: 30,
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
            gap: 20,
            width: "100%",
            maxWidth: 800,
          }}
        >
          {images.map((url, idx) => (
            <div
              key={idx}
              style={{
                background: "white",
                borderRadius: 8,
                padding: 10,
                boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
              }}
            >
              <img
                src={`http://localhost:8000${url}`}
                alt={`result ${idx}`}
                style={{
                  width: "100%",
                  borderRadius: 6,
                }}
              />
              <p style={{ marginTop: 8, fontSize: 14, color: "#555" }}>
                결과 이미지 {idx + 1}
              </p>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
