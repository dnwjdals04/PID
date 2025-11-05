# PID Project (AI 기반 영상 개인정보 자동 비식별화)

## 📌 개요
이 프로젝트는 FastAPI (백엔드) + Next.js (프론트엔드) 구조로,
영상 속 얼굴, 객체(번호판 등) 등을 자동으로 탐지하고
마스킹을 지원하는 서비스입니다.

---

## 📂 프로젝트 구조
```bash
# PID Project (AI 기반 영상 개인정보 자동 비식별화)

## 📌 개요
이 프로젝트는 FastAPI (백엔드) + Next.js (프론트엔드) 구조로,
영상 속 얼굴, 객체(번호판 등) 등을 자동으로 탐지하고
마스킹을 지원하는 서비스입니다.

---

## 📂 프로젝트 구조
```bash
PID/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes.py
│   │   └── services/
│   │       ├── ai_engine.py
│   │       ├── preprocess.py
│   │       ├── combine.py
│   │       ├── state.py
│   │       └── models/
│   │           └──best.pt
│   └── requirements.txt
│   
│
├── frontend/
│   ├── app/
│   │   ├── page.js 
│   │   ├── processing/[id]/page.js
│   │   └── result/[id]/page.js 
│   ├── components/
│   │   ├── UploadCard.js
│   │   ├── ProgressBar.js
│   │   └── VideoViewer.js
│   ├── lib/
│   │   └── api.js
│   ├── styles/
│   │   ├── glass.css
│   │   └── globals.css
│   ├── package.json
│   ├── package-lock.json
│   └── next.config.js
│   
└── README.md


```

---

## ⚙️ 환경 세팅

### 1. 백엔드 (FastAPI + AI 엔진)
```
cd backend
python3 -m venv venv
source venv/bin/activate   # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
# Python==3.10.12
uvicorn app.main:app --reload --port 8000
```

### 2. 프론트엔드 (Next.js)
```
cd frontend
npm install
npm run dev
```
