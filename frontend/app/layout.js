import "../styles/globals.css";
import "../styles/glass.css";

export const metadata = {
  title: "AI-VAMOS",
  description: "AI 기반 영상 비식별화 시스템",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>
        <main className="main-container">{children}</main>
      </body>
    </html>
  );
}
