from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from src.db import supabase
from pydantic import BaseModel
from src.models import DeviceCreate, DeviceUpdate
from src.routers.events import push_event
router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)

# ---------------- CREATE ----------------
@router.post("/")
def create_device(device: DeviceCreate):
    try:
        supabase.table("devices").insert(
            {"device_id": device.device_id, "user_id": device.user_id}
        ).execute()
        return {"message": "Device registered successfully", "device_id": device.device_id}
    except Exception:
        raise HTTPException(status_code=400, detail="Device ID already exists or invalid user_id.")


@router.get("/available")
def get_available_devices():
    response = (
        supabase.table("devices")
        .select("device_id, status, last_seen")
        .is_("user_id", "null")
        .execute()
    )
    return response.data or []

@router.post("/link")
def link_device(payload: dict):
    device_id = payload.get("device_id")
    user_id = payload.get("user_id")

    existing = supabase.table("devices").select("user_id").eq("device_id", device_id).limit(1).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Device not found")
    if existing.data[0].get("user_id"):
        raise HTTPException(status_code=400, detail="Device already linked")

    supabase.table("devices").update({"user_id": user_id}).eq("device_id", device_id).execute()
    return {"status": "linked"}

@router.post("/unlink")
def unlink_device(payload: dict):
    device_id = payload.get("device_id")
    user_id = payload.get("user_id")

    existing = supabase.table("devices").select("user_id").eq("device_id", device_id).limit(1).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Device not found")
    if existing.data[0].get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Device not linked to this account")

    supabase.table("devices").update({"user_id": None}).eq("device_id", device_id).execute()
    return {"status": "unlinked"}

class DeviceRegister(BaseModel):
    device_id: str

@router.post("/register")
def register_device(device: DeviceRegister):
    existing = supabase.table("devices").select("device_id", "user_id").eq("device_id", device.device_id).limit(1).execute()
    if existing.data:
        supabase.table("devices").update({
            "status": "online",
            "last_seen": datetime.now(timezone.utc).isoformat()
        }).eq("device_id", device.device_id).execute()
        return {"status": "online", "linked": existing.data[0].get("user_id") is not None}

    supabase.table("devices").insert({
        "device_id": device.device_id,
        "status": "online",
    }).execute()
    return {"status": "registered", "linked": False}
    
# ---------------- READ (User's Devices) ----------------
@router.get("/user/{user_id}")
def get_user_devices(user_id: int):
    response = supabase.table("devices").select("*").eq("user_id", user_id).execute()
    return response.data or []


# ---------------- READ (Single) ----------------
@router.get("/{device_id}")
def get_device(device_id: str):
    response = supabase.table("devices").select("*").eq("device_id", device_id).limit(1).execute()
    result = response.data[0] if response.data else None

    if not result:
        raise HTTPException(status_code=404, detail="Device not found")

    return result

# ---------------- UPDATE (Heartbeat/Settings) ----------------
@router.patch("/{device_id}")
def update_device(device_id: str, updates: DeviceUpdate):
    update_data = updates.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")

    exists_response = supabase.table("devices").select("device_id").eq("device_id", device_id).limit(1).execute()
    if not exists_response.data:
        raise HTTPException(status_code=404, detail="Device not found")

    update_data["last_seen"] = datetime.now(timezone.utc).isoformat()
    supabase.table("devices").update(update_data).eq("device_id", device_id).execute()

    push_event(device_id, "settings_updated", update_data)

    return {"message": "Live status updated", "fields": list(update_data.keys())}

