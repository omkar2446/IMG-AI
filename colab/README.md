# Google Colab SDXL API

Use `sdxl_colab_api.py` in Colab (or adapt from `sdxl_colab_api.ipynb`).

## What this API provides

- Stable Diffusion XL model: `stabilityai/stable-diffusion-xl-base-1.0`
- GPU-only generation with memory-aware defaults
- Public endpoint via ngrok
- Optional bearer-token protection
- Health endpoint and OpenAPI docs

## Environment variables (optional)

- `HF_TOKEN` for gated model download
- `COLAB_API_TOKEN` to protect `/generate` with `Authorization: Bearer <token>`
- `NGROK_AUTHTOKEN` to use your ngrok account
- `COLAB_API_PORT` (default `8000`)
- `SDXL_DEFAULT_STEPS` (default `35`)
- `SDXL_DEFAULT_GUIDANCE` (default `7.5`)
- `SDXL_MAX_IMAGES` (default `4`)
- `SDXL_MAX_STEPS` (default `50`)

## Request body (`POST /generate`)

```json
{
  "prompt": "A futuristic city at sunrise",
  "negative_prompt": "blurry, low quality",
  "image_size": 1024,
  "num_images": 2,
  "num_inference_steps": 35,
  "guidance_scale": 7.5,
  "seed": 123456
}
```

`image_size` must be one of `512`, `768`, `1024`.

## Response

```json
{
  "images": ["<base64_png>", "<base64_png>"],
  "seed": 123456
}
```

## Run flow

1. Open Colab and switch runtime to `GPU`.
2. Install dependencies from the script header command.
3. Run script cells.
4. Copy printed URL for `/generate` and set backend `COLAB_API_URL` to it.
5. Optionally verify `/health` and `/docs` URLs.
