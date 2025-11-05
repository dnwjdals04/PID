// next.config.js
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/result_video/:path*",
        destination: "http://localhost:8000/result_video/:path*", // FastAPI로 프록시
      },
    ];
  },
};

module.exports = nextConfig;
