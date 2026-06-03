from fastapi import APIRouter, HTTPException
from src.db import supabase
from pydantic import BaseModel
from src.routers.events import push_event

router = APIRouter(prefix="/geofence", tags=["Geofence"])

class GeofenceSchema(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    radius_meters: float

@router.post("/set")
def set_geofence(data: GeofenceSchema):
    try:
        device_response = (
            supabase.table("devices")
            .select("user_id")
            .eq("device_id", data.device_id)
            .limit(1)
            .execute()
        )
        user_id = device_response.data[0]["user_id"] if device_response.data else None
        supabase.table("geofences").upsert(
            {
                "device_id": data.device_id,
                "latitude": data.latitude,
                "longitude": data.longitude,
                "radius_meters": data.radius_meters,
                "user_id": user_id,
            },
            on_conflict="device_id",
        ).execute()
        push_event(data.device_id, "geofence_updated", {
            "latitude": data.latitude,
            "longitude": data.longitude,
            "radius_meters": data.radius_meters,
        })
        return {"status": "success", "message": "Geofence synchronized"}
    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save geofence")

@router.get("/{device_id}")
def get_geofence(device_id: str):
    response = (
        supabase.table("geofences")
        .select("latitude, longitude, radius_meters")
        .eq("device_id", device_id)
        .limit(1)
        .execute()
    )
    result = response.data[0] if response.data else None
    if not result:
        return {"latitude": None, "longitude": None, "radius_meters": None}
    return result