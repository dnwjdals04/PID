"use client";
import { useEffect, useState } from "react";
import axios from "../../../lib/api";
import VideoCompareCard from "../../../components/VideoCompareCard";
import LoadingSkeleton from "../../../components/LoadingSkeleton";

export default function ResultPage({ params }) {
  const { id } = params;
  const [data, setData] = useState(null);

  useEffect(() => {
    axios.get(`/result/${id}`).then((res) => setData(res.data));
  }, [id]);

  if (!data) return <LoadingSkeleton />;

  return (
    <div className="page-wrapper">
      <h2>결과 보기</h2>
      <VideoCompareCard original={data.original_url} masked={data.masked_url} />
    </div>
  );
}
