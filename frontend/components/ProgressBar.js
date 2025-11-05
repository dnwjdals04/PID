export default function ProgressBar({ progress }) {
  return (
    <div className="progress-bar-wrapper">
      <div
        className="progress-bar-fill"
        style={{ width: `${progress}%` }}
      ></div>
    </div>
  );
}
