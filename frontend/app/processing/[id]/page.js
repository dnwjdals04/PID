"use client";
import { useEffect, useState } from "react";
import ProgressBar from "../../../components/ProgressBar";

export default function ProcessingPage({ params }) {
  const { id } = params;
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("AI 준비 중...");
  const [done, setDone] = useState(false);

  useEffect(() => {
    // ✅ SSE 연결
    const eventSource = new EventSource(`http://localhost:8000/progress-stream/${id}`);

    eventSource.onmessage = (event) => {
      const [p, stageRaw, status] = event.data.split(",");
      const progressVal = parseInt(p);
      setProgress(progressVal);

      const stageText = {
        splitting: "🎞 영상 분할 중...",
        extracting: "📸 프레임 추출 중...",
        masking: "🤖 AI가 얼굴/번호판 마스킹 중...",
        combining_final: "🎬 영상 재조합 중...",
        done: "✅ 분석 완료!",
      }[stageRaw] || "AI 분석 중...";

      setStage(stageText);

      if (status === "done" && progressVal >= 100) {
        setDone(true);
        setStage("✅ 분석 완료! 결과 페이지로 이동합니다...");
        eventSource.close();
        setTimeout(() => {
          window.location.href = `/result/${id}`;
        }, 1500);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE 연결 오류:", err);
      eventSource.close();
    };

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
