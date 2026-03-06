from pydantic import BaseModel, Field


class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    negative_prompt: str = Field(default="", max_length=2000)
    image_size: int = Field(default=1024)
    num_images: int = Field(default=1)
    input_image: str | None = Field(default=None)
    strength: float = Field(default=0.55, ge=0.1, le=0.95)


class GenerateImageResponse(BaseModel):
    images: list[str]
