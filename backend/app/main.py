import asyncio
import base64
import io
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import torch
from diffusers import AutoPipelineForImage2Image, DiffusionPipeline
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps

from .schemas import GenerateImageRequest, GenerateImageResponse


load_dotenv()

MODEL_ID = os.getenv("SDXL_MODEL_ID", "stabilityai/stable-diffusion-xl-base-1.0").strip()
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
_requested_device = os.getenv("SDXL_DEVICE", "auto").strip().lower()
DEFAULT_STEPS = int(os.getenv("SDXL_DEFAULT_STEPS", "35"))
DEFAULT_GUIDANCE = float(os.getenv("SDXL_DEFAULT_GUIDANCE", "7.5"))
MAX_IMAGES = int(os.getenv("SDXL_MAX_IMAGES", "4"))

if _requested_device in {"", "auto"}:
    SDXL_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
elif _requested_device.startswith("cuda") and not torch.cuda.is_available():
    print("Warning: SDXL_DEVICE=cuda requested but CUDA is unavailable. Falling back to CPU.")
    SDXL_DEVICE = "cpu"
else:
    SDXL_DEVICE = _requested_device

BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_DIR = BASE_DIR / "generated"
HISTORY_FILE = BASE_DIR / "history.json"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="SDXL Backend API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/generated-images", StaticFiles(directory=str(GENERATED_DIR)), name="generated-images")

_txt2img_pipeline: DiffusionPipeline | None = None
_img2img_pipeline: AutoPipelineForImage2Image | None = None
_pipeline_lock = threading.Lock()


def _load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_history(items: list[dict]) -> None:
    HISTORY_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")


def _save_image_from_base64(image_b64: str, prompt: str) -> dict:
    image_id = str(uuid4())
    file_path = GENERATED_DIR / f"{image_id}.png"
    file_path.write_bytes(base64.b64decode(image_b64))

    return {
        "id": image_id,
        "url": f"/generated-images/{image_id}.png",
        "prompt": prompt,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }


def _pil_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _dtype_for_device(device: str) -> torch.dtype:
    return torch.float16 if device.startswith("cuda") else torch.float32


def _get_txt2img_pipeline() -> DiffusionPipeline:
    global _txt2img_pipeline
    if _txt2img_pipeline is not None:
        return _txt2img_pipeline

    with _pipeline_lock:
        if _txt2img_pipeline is None:
            dtype = _dtype_for_device(SDXL_DEVICE)
            pipe = DiffusionPipeline.from_pretrained(
                MODEL_ID,
                torch_dtype=dtype,
                use_safetensors=True,
                token=HF_TOKEN if HF_TOKEN else None,
            )
            pipe = pipe.to(SDXL_DEVICE)
            pipe.enable_attention_slicing()
            _txt2img_pipeline = pipe

    return _txt2img_pipeline


def _get_img2img_pipeline() -> AutoPipelineForImage2Image:
    global _img2img_pipeline
    if _img2img_pipeline is not None:
        return _img2img_pipeline

    with _pipeline_lock:
        if _img2img_pipeline is None:
            dtype = _dtype_for_device(SDXL_DEVICE)
            pipe = AutoPipelineForImage2Image.from_pretrained(
                MODEL_ID,
                torch_dtype=dtype,
                use_safetensors=True,
                token=HF_TOKEN if HF_TOKEN else None,
            )
            pipe = pipe.to(SDXL_DEVICE)
            pipe.enable_attention_slicing()
            _img2img_pipeline = pipe

    return _img2img_pipeline


def _decode_input_image(image_data: str, image_size: int) -> Image.Image:
    raw = image_data.strip()
    if "," in raw:
        raw = raw.split(",", 1)[1]
    image_bytes = base64.b64decode(raw)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return ImageOps.fit(image, (image_size, image_size), method=Image.Resampling.LANCZOS)


def _generate_local_images(payload: GenerateImageRequest) -> list[str]:
    input_image = _decode_input_image(payload.input_image, payload.image_size) if payload.input_image else None

    if input_image:
        pipe = _get_img2img_pipeline()
        with _pipeline_lock:
            if SDXL_DEVICE.startswith("cuda"):
                with torch.inference_mode(), torch.autocast("cuda"):
                    result = pipe(
                        prompt=payload.prompt,
                        negative_prompt=payload.negative_prompt,
                        image=input_image,
                        strength=payload.strength,
                        num_images_per_prompt=payload.num_images,
                        num_inference_steps=DEFAULT_STEPS,
                        guidance_scale=DEFAULT_GUIDANCE,
                    )
            else:
                with torch.inference_mode():
                    result = pipe(
                        prompt=payload.prompt,
                        negative_prompt=payload.negative_prompt,
                        image=input_image,
                        strength=payload.strength,
                        num_images_per_prompt=payload.num_images,
                        num_inference_steps=DEFAULT_STEPS,
                        guidance_scale=DEFAULT_GUIDANCE,
                    )
    else:
        pipe = _get_txt2img_pipeline()
        with _pipeline_lock:
            if SDXL_DEVICE.startswith("cuda"):
                with torch.inference_mode(), torch.autocast("cuda"):
                    result = pipe(
                        prompt=payload.prompt,
                        negative_prompt=payload.negative_prompt,
                        height=payload.image_size,
                        width=payload.image_size,
                        num_images_per_prompt=payload.num_images,
                        num_inference_steps=DEFAULT_STEPS,
                        guidance_scale=DEFAULT_GUIDANCE,
                    )
            else:
                with torch.inference_mode():
                    result = pipe(
                        prompt=payload.prompt,
                        negative_prompt=payload.negative_prompt,
                        height=payload.image_size,
                        width=payload.image_size,
                        num_images_per_prompt=payload.num_images,
                        num_inference_steps=DEFAULT_STEPS,
                        guidance_scale=DEFAULT_GUIDANCE,
                    )

    return [_pil_to_base64(img) for img in result.images]


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "mode": "local",
        "model": MODEL_ID,
        "device": SDXL_DEVICE,
        "pipelines_loaded": {
            "txt2img": _txt2img_pipeline is not None,
            "img2img": _img2img_pipeline is not None,
        },
    }


@app.get("/api/history")
async def get_history():
    items = _load_history()
    return {"items": items[::-1]}


@app.post("/api/generate-image", response_model=GenerateImageResponse)
async def generate_image(payload: GenerateImageRequest):
    if payload.image_size not in {512, 768, 1024}:
        raise HTTPException(status_code=400, detail="image_size must be one of: 512, 768, 1024")

    if payload.num_images < 1 or payload.num_images > MAX_IMAGES:
        raise HTTPException(status_code=400, detail=f"num_images must be between 1 and {MAX_IMAGES}")

    try:
        images = await asyncio.to_thread(_generate_local_images, payload)
    except RuntimeError as exc:
        if "out of memory" in str(exc).lower() and torch.cuda.is_available():
            torch.cuda.empty_cache()
            raise HTTPException(
                status_code=500,
                detail="CUDA out of memory. Try smaller image_size or fewer images.",
            ) from exc
        raise HTTPException(status_code=500, detail=f"Local SDXL generation failed: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Local SDXL generation failed: {exc}") from exc

    if not images:
        raise HTTPException(status_code=500, detail="No images generated")

    history_items = _load_history()
    new_entries = [_save_image_from_base64(img_b64, payload.prompt) for img_b64 in images]
    history_items.extend(new_entries)
    _save_history(history_items)

    return {"images": images}
