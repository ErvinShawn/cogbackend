import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Dict
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Events"])

# In-memory registry: device_id -> list of active queues
_device_queues: Dict[str, list[asyncio.Queue]] = {}


def _get_or_create_queues(device_id: str) -> list:
    if device_id not in _device_queues:
        _device_queues[device_id] = []
    return _device_queues[device_id]


def push_event(device_id: str, event: str, data: dict = None):

    if data is None:
        data = {}

    queues = _device_queues.get(device_id, [])

    if not queues:
        logger.info(
            f"[SSE] No active listeners for device {device_id}"
        )
        return

    message = json.dumps({
        "event": event,
        "data": data
    })

    for q in queues:
        q.put_nowait(message)

    logger.info(
        f"[SSE] Sent {event} to {device_id}"
    )


@router.get("/events/{device_id}")
async def sse_stream(device_id: str):
    queue: asyncio.Queue = asyncio.Queue()
    queues = _get_or_create_queues(device_id)
    queues.append(queue)
    logger.info(f"[SSE] Device connected: {device_id}")

    async def stream():
        # Send connected confirmation
        yield f"data: {json.dumps({'event': 'connected', 'data': {}})}\n\n"
        try:
            while True:
                try:
                    # Ping every 30s to keep connection alive
                    message = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event': 'ping', 'data': {}})}\n\n"
        finally:
            queues.remove(queue)
            logger.info(f"[SSE] Device disconnected: {device_id}")

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Important for Render/nginx proxies
        }
    )
