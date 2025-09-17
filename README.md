# PID Project (AI 기반 영상 개인정보 자동 비식별화)

## 📌 개요
이 프로젝트는 **FastAPI (백엔드)** + **Next.js (프론트엔드)** 구조로,
영상 속 얼굴, 객체(번호판 등), 텍스트(OCR)를 자동으로 탐지하고
마스킹/시각화를 지원하는 서비스입니다.

---

## 📂 프로젝트 구조
PID/
├── backend/ # FastAPI 백엔드
│ ├── app/
│ │ ├── main.py # FastAPI 엔트리포인트
│ │ ├── routes.py # 업로드/분석 API
│ │ ├── models.py # 데이터 모델 (Pydantic)
│ │ └── services/ # 서비스 모듈
│ │ ├── ai_engine.py # YOLO + PaddleOCR 분석
│ │ ├── preprocess.py # 영상 전처리
│ │ ├── mock_ai.py # 임시 분석 (샘플용)
│ │ └── init.py
│ └── requirements.txt
│
├── frontend/ # Next.js 프론트엔드
│ ├── app/
│ │ ├── page.js # 업로드 + 분석 결과 UI
│ │ └── layout.js # 기본 레이아웃
│ ├── components/
│ │ └── VideoPlayer.js
│ ├── package.json
│ ├── package-lock.json
│ └── next.config.js
└── README.md


---

## ⚙️ 환경 세팅

### 1. 백엔드 (FastAPI + AI 엔진)
```
cd backend
python -m venv venv
source venv/bin/activate   # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. 프론트엔드 (Next.js)
```
cd frontend
npm install
npm run dev
```
