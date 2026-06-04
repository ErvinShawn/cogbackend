import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Dict
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Events"])

_device_queues: Dict[str, list] = {}


def _get_or_create_queues(device_id: str) -> list:
    if device_id not in _device_queues:
        _device_queues[device_id] = []
    return _device_queues[device_id]


def push_event(device_id: str, event: str, data: dict = {}):
    """Sync-safe — can be called from regular def routes."""
    queues = _device_queues.get(device_id, [])
    if not queues:
        logger.info(f"[SSE] No active listeners for {device_id}")
        return
    message = json.dumps({"event": event, "data": data})
    for q in queues:
        try:
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(q.put_nowait, message)
        except Exception as e:
            logger.warning(f"[SSE] push failed: {e}")


@router.get("/events/{device_id}")
async def sse_stream(device_id: str):
    queue: asyncio.Queue = asyncio.Queue()
    queues = _get_or_create_queues(device_id)
    queues.append(queue)
    logger.info(f"[SSE] Device connected: {device_id}")

    async def stream():
        yield f"data: {json.dumps({'event': 'connected', 'data': {}})}\n\n"
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event': 'ping', 'data': {}})}\n\n"
        finally:
            if queue in queues:
                queues.remove(queue)
            logger.info(f"[SSE] Device disconnected: {device_id}")

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )