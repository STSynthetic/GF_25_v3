from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps
from pydantic import BaseModel, Field


class PreprocessConfig(BaseModel):
    auto_orient: bool = Field(default=True, description="Apply EXIF-based orientation")
    normalize_mode: bool = Field(default=True, description="Convert image to RGB mode")
    max_dimension: int = Field(default=2048, ge=1, description="Max side length for resizing (fit)")
    thumbnail_size: int = Field(default=256, ge=1, description="Max side for thumbnail")
    thumbnail_suffix: str = Field(
        default=".thumb.jpg",
        description="Output suffix for thumbnail file",
    )


class PreprocessResult(BaseModel):
    processed_path: str = Field(description="Path to processed image")
    width: int = Field(ge=1, description="Processed image width")
    height: int = Field(ge=1, description="Processed image height")
    mode: str = Field(description="Processed image mode, typically RGB")
    thumbnail_path: str | None = Field(default=None, description="Thumbnail path if generated")
    thumb_width: int | None = Field(default=None, description="Thumbnail width")
    thumb_height: int | None = Field(default=None, description="Thumbnail height")


@dataclass
class _OpenResult:
    image: Image.Image
    orientation_applied: bool


class ImagePreprocessor:
    def __init__(self, cfg: PreprocessConfig) -> None:
        self.cfg = cfg

    async def process(
        self,
        src_path: str,
        out_path: str,
        *,
        make_thumbnail: bool = True,
    ) -> PreprocessResult:
        # Do heavy operations in executor
        loop = asyncio.get_running_loop()

        def _work() -> PreprocessResult:
            with Image.open(src_path) as im:
                img = im
                if self.cfg.auto_orient:
                    img = ImageOps.exif_transpose(img)
                if self.cfg.normalize_mode and img.mode != "RGB":
                    img = img.convert("RGB")

                # Resize to fit within max_dimension preserving aspect ratio
                if max(img.size) > self.cfg.max_dimension:
                    img.thumbnail(
                        (self.cfg.max_dimension, self.cfg.max_dimension),
                        Image.Resampling.LANCZOS,
                    )

                # Save processed
                Path(out_path).parent.mkdir(parents=True, exist_ok=True)
                img.save(out_path, format="JPEG", quality=92, optimize=True)
                width, height = img.size

                thumb_path: str | None = None
                tw: int | None = None
                th: int | None = None
                if make_thumbnail:
                    thumb = img.copy()
                    thumb.thumbnail(
                        (self.cfg.thumbnail_size, self.cfg.thumbnail_size),
                        Image.Resampling.LANCZOS,
                    )
                    thumb_path = out_path + self.cfg.thumbnail_suffix
                    thumb.save(thumb_path, format="JPEG", quality=88, optimize=True)
                    tw, th = thumb.size

                return PreprocessResult(
                    processed_path=out_path,
                    width=width,
                    height=height,
                    mode=img.mode,
                    thumbnail_path=thumb_path,
                    thumb_width=tw,
                    thumb_height=th,
                )

        return await loop.run_in_executor(None, _work)
