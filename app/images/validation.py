from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from pydantic import BaseModel, Field

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class ValidationConfig(BaseModel):
    max_bytes: int = Field(
        default=100 * 1024 * 1024,
        ge=1,
        description="Max allowed file size in bytes",
    )
    min_width: int = Field(default=640, ge=1, description="Minimum width in pixels")
    min_height: int = Field(default=480, ge=1, description="Minimum height in pixels")
    max_width: int = Field(default=4096, ge=1, description="Maximum width in pixels")
    max_height: int = Field(default=4096, ge=1, description="Maximum height in pixels")


class ValidationResult(BaseModel):
    ok: bool = Field(description="Whether validation passed")
    format: str | None = Field(default=None, description="Detected image format")
    width: int | None = Field(default=None, description="Image width")
    height: int | None = Field(default=None, description="Image height")
    reason: str | None = Field(default=None, description="Reason for failure if not ok")


@dataclass
class _ImageInfo:
    format: str
    width: int
    height: int


class ImageValidator:
    def __init__(self, cfg: ValidationConfig) -> None:
        self.cfg = cfg

    async def validate_path(self, path: str) -> ValidationResult:
        p = Path(path)
        if not p.exists():
            return ValidationResult(ok=False, reason="file not found")

        # size
        size = p.stat().st_size
        if size > self.cfg.max_bytes:
            return ValidationResult(
                ok=False,
                reason=f"file too large: {size} > {self.cfg.max_bytes}",
            )

        # inspect image in executor
        try:
            info = await self._inspect(path)
        except Exception as ex:  # pragma: no cover (covered via invalid cases)
            return ValidationResult(ok=False, reason=f"invalid image: {ex}")

        if info.format not in ALLOWED_FORMATS:
            return ValidationResult(
                ok=False,
                format=info.format,
                width=info.width,
                height=info.height,
                reason=f"unsupported format: {info.format}",
            )

        if not (self.cfg.min_width <= info.width <= self.cfg.max_width):
            return ValidationResult(
                ok=False,
                format=info.format,
                width=info.width,
                height=info.height,
                reason=f"width out of bounds: {info.width}",
            )
        if not (self.cfg.min_height <= info.height <= self.cfg.max_height):
            return ValidationResult(
                ok=False,
                format=info.format,
                width=info.width,
                height=info.height,
                reason=f"height out of bounds: {info.height}",
            )

        return ValidationResult(ok=True, format=info.format, width=info.width, height=info.height)

    async def _inspect(self, path: str) -> _ImageInfo:
        loop = asyncio.get_running_loop()

        def _open() -> _ImageInfo:
            with Image.open(path) as im:
                fmt = (im.format or "").upper()
                w, h = im.size
                return _ImageInfo(format=fmt, width=w, height=h)

        return await loop.run_in_executor(None, _open)
