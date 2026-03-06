# Frontend (React + Tailwind)

## Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

It proxies `/api` requests to `http://localhost:8000`.

## Features

- Prompt + negative prompt inputs
- Size selector (`512`, `768`, `1024`)
- Number of images selector
- Generation button with loading overlay
- Image gallery with download buttons
- Responsive dark-mode layout
- History display (from backend)
