from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from src.db import supabase
from src.models import DeviceCreate, DeviceUpdate

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

# ---------------- READ (Single) ----------------
@router.get("/{device_id}")
def get_device(device_id: str):
    response = supabase.table("devices").select("*").eq("device_id", device_id).limit(1).execute()
    result = response.data[0] if response.data else None

    if not result:
        raise HTTPException(status_code=404, detail="Device not found")

    return result

# ---------------- READ (User's Devices) ----------------
@router.get("/user/{user_id}")
def get_user_devices(user_id: int):
    response = supabase.table("devices").select("*").eq("user_id", user_id).execute()
    return response.data or []

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

    return {"message": "Live status updated", "fields": list(update_data.keys())}