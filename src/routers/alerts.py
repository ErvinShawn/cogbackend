from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from src.db import supabase
from src.models import DeviceAlertCreate

router = APIRouter(tags=["Alerts"])
ALERTS_MEMORY = []

ALERT_METADATA = {
    "geofence_breach": {
        "title": "Patient exited home boundary",
        "severity": "Critical",
    },
    "fall_risk": {
        "title": "Fall risk movement detected",
        "severity": "Critical",
    },
    "missed_medication": {
        "title": "Missed medication reminder",
        "severity": "Moderate",
    },
    "device_offline": {
        "title": "Device connection lost",
        "severity": "Moderate",
    },
}


def _normalize_alert(alert: DeviceAlertCreate, user_id: int) -> dict:
    alert_key = alert.alert_type.strip().lower().replace(" ", "_")
    metadata = ALERT_METADATA.get(alert_key, {})

    return {
        "id": int(datetime.now(timezone.utc).timestamp() * 1000),
        "user_id": user_id,
        "device_id": alert.device_id,
        "alert_type": alert_key,
        "title": alert.title or metadata.get("title") or alert.alert_type.replace("_", " ").title(),
        "severity": alert.severity or metadata.get("severity") or "Moderate",
        "created_at": alert.timestamp or datetime.now(timezone.utc).isoformat(),
    }


def _store_alert(payload: dict):
    try:
        response = supabase.table("alerts").insert(payload).execute()
        if response.data:
            return response.data[0]
    except Exception:
        pass

    ALERTS_MEMORY.insert(0, payload)
    return payload


def _get_alerts_for_user(user_id: int):
    try:
        response = (
            supabase.table("alerts")
            .select("id, user_id, device_id, alert_type, title, severity, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        if response.data is not None:
            return response.data
    except Exception:
        pass

    return [alert for alert in ALERTS_MEMORY if alert.get("user_id") == user_id]


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

    user_id = device_response.data[0].get("user_id")
    payload = _normalize_alert(alert, user_id)
    stored_alert = _store_alert(payload)

    return {
        "status": "alert received",
        "device": alert.device_id,
        "alert": stored_alert,
    }


@router.get("/alerts/user/{user_id}")
def get_user_alerts(user_id: int):
    return _get_alerts_for_user(user_id)
