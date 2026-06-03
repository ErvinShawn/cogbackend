from datetime import datetime, timezone
import logging
from fastapi import APIRouter, HTTPException
from src.db import supabase
from src.models import DeviceAlertCreate

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Alerts"])

ALERT_METADATA = {
    "geofence_breach":   {"title": "Patient exited home boundary", "severity": "Critical"},
    "fall_risk":         {"title": "Fall risk movement detected",  "severity": "Critical"},
    #"missed_medication": {"title": "Missed medication reminder",   "severity": "Moderate"},
    "device_offline":    {"title": "Device connection lost",       "severity": "Moderate"},
}

def _normalize_alert(alert: DeviceAlertCreate, user_id: int) -> dict:
    alert_key = alert.alert_type.strip().lower().replace(" ", "_")
    metadata = ALERT_METADATA.get(alert_key, {})
    return {
        "user_id": user_id,
        "device_id": alert.device_id,
        "alert_type": alert_key,
        "title": alert.title or metadata.get("title") or alert_key.replace("_", " ").title(),
        "severity": alert.severity or metadata.get("severity") or "Moderate",
        "created_at": alert.timestamp or datetime.now(timezone.utc).isoformat(),
    }

def _send_push_notifications(user_id: int, title: str, body: str):
    try:
        token_response = (
            supabase.table("push_tokens")
            .select("token")
            .eq("user_id", user_id)
            .execute()
        )
        tokens = [row["token"] for row in (token_response.data or [])]
        if not tokens:
            return

        import httpx
        messages = [{"to": t, "title": title, "body": body, "sound": "default"} for t in tokens]
        httpx.post("https://exp.host/--/api/v2/push/send", json=messages, timeout=5)
    except Exception as e:
        logger.error(f"Push notification failed: {e}")

@router.post("/device/alert")
def create_device_alert(alert: DeviceAlertCreate):
    device_response = (
        supabase.table("devices")
        .select("user_id")
        .eq("device_id", alert.device_id)
        .limit(1)
        .execute()
    )
    if not device_response.data:
        raise HTTPException(status_code=404, detail="Device not found")

    user_id = device_response.data[0]["user_id"]
    payload = _normalize_alert(alert, user_id)

    response = supabase.table("alerts").insert(payload).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to store alert")
    stored_alert = response.data[0]

    _send_push_notifications(user_id, payload["title"], f"Alert: {payload['alert_type']}")

    return {"status": "alert received", "device": alert.device_id, "alert": stored_alert}

@router.get("/alerts/user/{user_id}")
def get_user_alerts(user_id: int):
    response = (
        supabase.table("alerts")
        .select("id, user_id, device_id, alert_type, title, severity, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []

