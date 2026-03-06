"""SDXL Colab API server.

Run in Google Colab with GPU runtime.

Suggested install command in a notebook cell:
!pip -q install diffusers transformers accelerate safetensors fastapi uvicorn pyngrok nest-asyncio python-multipart
"""

import base64
import io
import os
import threading
from typing import Optional

import nest_asyncio
import torch
import uvicorn
from diffusers import DiffusionPipeline
from fastapi import FastAPI, Header, HTTPException
from PIL import Image
from pydantic import BaseModel, Field, field_validator
from pyngrok import ngrok


MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
API_TOKEN = os.getenv("COLAB_API_TOKEN", "").strip()
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "").strip()
HOST = os.getenv("COLAB_API_HOST", "0.0.0.0")
PORT = int(os.getenv("COLAB_API_PORT", "8000"))

DEFAULT_STEPS = int(os.getenv("SDXL_DEFAULT_STEPS", "35"))
DEFAULT_GUIDANCE = float(os.getenv("SDXL_DEFAULT_GUIDANCE", "7.5"))
MAX_IMAGES = int(os.getenv("SDXL_MAX_IMAGES", "4"))
MAX_STEPS = int(os.getenv("SDXL_MAX_STEPS", "50"))

if not torch.cuda.is_available():
    raise RuntimeError("CUDA GPU is required. In Colab, change runtime to GPU.")

DTYPE = torch.float16


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    negative_prompt: str = Field(default="", max_length=2000)
    image_size: int = Field(default=1024)
    num_images: int = Field(default=1)
    num_inference_steps: int = Field(default=DEFAULT_STEPS)
    guidance_scale: float = Field(default=DEFAULT_GUIDANCE)
    seed: Optional[int] = Field(default=None)

    @field_validator("image_size")
    @classmethod
    def validate_image_size(cls, value: int) -> int:
        if value not in {512, 768, 1024}:
            raise ValueError("image_size must be one of: 512, 768, 1024")
        return value

    @field_validator("num_images")
    @classmethod
    def validate_num_images(cls, value: int) -> int:
        if value < 1 or value > MAX_IMAGES:
            raise ValueError(f"num_images must be between 1 and {MAX_IMAGES}")
        return value

    @field_validator("num_inference_steps")
    @classmethod
    def validate_steps(cls, value: int) -> int:
        if value < 1 or value > MAX_STEPS:
            raise ValueError(f"num_inference_steps must be between 1 and {MAX_STEPS}")
        return value

    @field_validator("guidance_scale")
    @classmethod
    def validate_guidance(cls, value: float) -> float:
        if value < 0 or value > 20:
            raise ValueError("guidance_scale must be between 0 and 20")
        return value


class GenerateResponse(BaseModel):
    images: list[str]
    seed: int


def _pil_to_base64(img: Image.Image) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _authorize(authorization: Optional[str]) -> None:
    if not API_TOKEN:
        return
    expected = f"Bearer {API_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _load_pipeline() -> DiffusionPipeline:
    pipe = DiffusionPipeline.from_pretrained(
        MODEL_ID,
        torch_dtype=DTYPE,
        use_safetensors=True,
        token=HF_TOKEN if HF_TOKEN else None,
    )
    pipe = pipe.to("cuda")
    pipe.enable_attention_slicing()
    return pipe


app = FastAPI(title="SDXL Colab API", version="1.1.0")
pipeline_lock = threading.Lock()
pipeline = _load_pipeline()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model": MODEL_ID,
        "device": "cuda",
        "max_images": MAX_IMAGES,
        "max_steps": MAX_STEPS,
    }


@app.post("/generate", response_model=GenerateResponse)
def generate(payload: GenerateRequest, authorization: Optional[str] = Header(default=None)) -> GenerateResponse:
    _authorize(authorization)

    seed = payload.seed if payload.seed is not None else int(torch.randint(0, 2**31 - 1, (1,)).item())
    generator = torch.Generator(device="cuda").manual_seed(seed)

    try:
        with pipeline_lock:
            with torch.inference_mode(), torch.autocast("cuda"):
                result = pipeline(
                    prompt=payload.prompt,
                    negative_prompt=payload.negative_prompt,
                    height=payload.image_size,
                    width=payload.image_size,
                    num_images_per_prompt=payload.num_images,
                    num_inference_steps=payload.num_inference_steps,
                    guidance_scale=payload.guidance_scale,
                    generator=generator,
                )

        images_b64 = [_pil_to_base64(img) for img in result.images]
        return GenerateResponse(images=images_b64, seed=seed)
    except RuntimeError as exc:
        if "out of memory" in str(exc).lower():
            torch.cuda.empty_cache()
            raise HTTPException(
                status_code=500,
                detail="CUDA out of memory. Try smaller image_size, fewer num_images, or lower num_inference_steps.",
            ) from exc
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}") from exc


# Colab-friendly startup
nest_asyncio.apply()

if NGROK_AUTHTOKEN:
    ngrok.set_auth_token(NGROK_AUTHTOKEN)

public_url = ngrok.connect(PORT).public_url
print(f"Public API URL: {public_url}/generate")
print(f"Health check URL: {public_url}/health")
print(f"OpenAPI docs URL: {public_url}/docs")

config = uvicorn.Config(app, host=HOST, port=PORT, log_level="info")
server = uvicorn.Server(config)
thread = threading.Thread(target=server.run, daemon=True)
thread.start()
