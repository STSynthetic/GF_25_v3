from __future__ import annotations

import asyncio
from pathlib import Path

from watchfiles import awatch

from app.config_loader import ConfigRegistry


async def watch_and_reload_configs(
    directory: Path,
    registry: ConfigRegistry,
    *,
    debounce_ms: int = 200,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Watch a directory for YAML changes and hot-reload configs.

    Uses watchfiles.awatch to monitor changes. Debounces bursts and refreshes
    the in-memory registry atomically via ConfigRegistry.refresh().
    """
    # Initial load
    registry.load_all_configs(directory)

    async for _changes in awatch(
        directory,
        debounce=debounce_ms / 1000.0,
        force_polling=True,
    ):
        registry.refresh(directory)
        if stop_event and stop_event.is_set():
            break


def start_config_watcher_task(
    directory: Path,
    registry: ConfigRegistry,
    *,
    debounce_ms: int = 200,
) -> tuple[asyncio.Task[None], asyncio.Event]:
    """Start the async watcher task and return (task, stop_event)."""
    stop_event: asyncio.Event = asyncio.Event()
    task = asyncio.create_task(
        watch_and_reload_configs(
            directory,
            registry,
            debounce_ms=debounce_ms,
            stop_event=stop_event,
        )
    )
    return task, stop_event
