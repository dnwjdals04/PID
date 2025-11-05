"use client";
import { useEffect, useState } from "react";
import ProgressBar from "../../../components/ProgressBar";

export default function ProcessingPage({ params }) {
  const { id } = params;

  // ✅ 상태 정의
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("AI 준비 중...");
  const [done, setDone] = useState(false);

  useEffect(() => {
    // --- 1️⃣ SSE 연결 ---
    const eventSource = new EventSource(`http://localhost:8000/progress-stream/${id}`);

    // --- 2️⃣ SSE 데이터 수신 ---
    eventSource.onmessage = (event) => {
      const [p, stageRaw, status] = event.data.split(",");
      const progressVal = parseInt(p);
      setProgress(progressVal);

      // 단계별 텍스트 표시
      const stageText = {
        splitting: "🎞 영상 분할 중...",
        extracting: "📸 프레임 추출 중...",
        masking: "🤖 AI가 얼굴/번호판 마스킹 중...",
        combining_final: "🎬 영상 재조합 중...",
        done: "✅ 분석 완료!",
      }[stageRaw] || "AI 분석 중...";

      setStage(stageText);

      // --- 3️⃣ 완료 시 리다이렉트 ---
      if (status === "done" && progressVal >= 100) {
        setDone(true);
        setStage("✅ 분석 완료! 결과 페이지로 이동합니다...");
        eventSource.close();
        setTimeout(() => {
          window.location.href = `/result/${id}`;
        }, 1500);
      }
    };

    // --- 5️⃣ 연결 에러 ---
    eventSource.onerror = (err) => {
      console.error("SSE 연결 오류:", err);
      eventSource.close();
    };

    // --- 6️⃣ 컴포넌트 unmount 시 종료 ---
    return () => {
      eventSource.close();
    };
  }, [id]);

  return (
    <div className="processing-wrapper">
      <h1>AI-VAMOS</h1>
      <p className="status-text">{stage}</p>
      <ProgressBar progress={progress} />
      <p className="percent-text">{progress}%</p>
    </div>
  );
}
