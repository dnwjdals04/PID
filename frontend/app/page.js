"use client";
import UploadCard from "../components/UploadCard";

export default function Home() {
  return (
    <>
      <div className="header-banner">AI-VAMOS</div>

      <div className="center-upload">
        <div className="page-wrapper">
          <h1>영상 업로드</h1>
          <UploadCard />
        </div>
      </div>
    </>
  );
}