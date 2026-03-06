# Backend (FastAPI + Local SDXL)

This backend runs Stable Diffusion XL directly (local machine), no Colab forwarding.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` (optional):
- `SDXL_MODEL_ID` model name
- `HF_TOKEN` if model access requires auth
- `SDXL_DEVICE` (`cuda` recommended, `cpu` works but is very slow)
- `SDXL_DEFAULT_STEPS`
- `SDXL_DEFAULT_GUIDANCE`
- `SDXL_MAX_IMAGES`

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

On first generation, model weights will download.

## API

- `POST /api/generate-image`
- `GET /api/history`
- `GET /api/health`
- `GET /generated-images/{file}` static generated image files

### Request body (`/api/generate-image`)

```json
{
  "prompt": "A futuristic city at sunrise",
  "negative_prompt": "blurry, low quality",
  "image_size": 1024,
  "num_images": 2,
  "input_image": "data:image/png;base64,...",
  "strength": 0.55
}
```

- `input_image` is optional. If present, backend runs image-to-image mode.
- `strength` controls how strongly the input photo is transformed (`0.1` to `0.95`).
