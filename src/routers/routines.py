# routines.py
from fastapi import APIRouter, HTTPException
from src.db import supabase
from src.routers.events import push_event
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/routines", tags=["Routines"])

class ReminderSchema(BaseModel):
    title: str
    description: Optional[str] = None
    time: str

class RoutineUpdate(BaseModel):
    device_id: str
    user_id: int
    reminder: ReminderSchema

def _push_for_user(user_id: int):
    device = supabase.table("devices").select("device_id").eq("user_id", user_id).limit(1).execute()
    if device.data:
        push_event(device.data[0]["device_id"], "routines_updated")

@router.post("/save")
def save_reminder(data: RoutineUpdate):
    try:
        existing_response = (
            supabase.table("routines")
            .select("reminders")
            .eq("user_id", data.user_id)
            .limit(1)
            .execute()
        )
        reminders = []
        if existing_response.data:
            reminders = existing_response.data[0].get("reminders") or []
        reminders.append({
            "title": data.reminder.title,
            "description": data.reminder.description,
            "time": data.reminder.time,
        })
        supabase.table("routines").upsert(
            {"device_id": data.device_id, "user_id": data.user_id, "reminders": reminders},
            on_conflict="user_id",
        ).execute()
        push_event(data.device_id, "routines_updated")
        return {"status": "success"}
    except Exception as e:
        print(f"Error saving routine: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")
def get_reminders(user_id: int):
    response = supabase.table("routines").select("reminders").eq("user_id", user_id).limit(1).execute()
    if not response.data:
        return []
    return response.data[0].get("reminders") or []

@router.put("/user/{user_id}/reminder/{index}")
def update_reminder(user_id: int, index: int, reminder: ReminderSchema):
    response = supabase.table("routines").select("reminders").eq("user_id", user_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="No routines found")
    reminders = response.data[0].get("reminders") or []
    if index < 0 or index >= len(reminders):
        raise HTTPException(status_code=404, detail="Reminder index out of range")
    reminders[index] = {"title": reminder.title, "description": reminder.description, "time": reminder.time}
    supabase.table("routines").update({"reminders": reminders}).eq("user_id", user_id).execute()
    _push_for_user(user_id)
    return {"status": "updated"}

@router.delete("/user/{user_id}/reminder/{index}")
def delete_reminder(user_id: int, index: int):
    response = supabase.table("routines").select("reminders").eq("user_id", user_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="No routines found")
    reminders = response.data[0].get("reminders") or []
    if index < 0 or index >= len(reminders):
        raise HTTPException(status_code=404, detail="Reminder index out of range")
    reminders.pop(index)
    supabase.table("routines").update({"reminders": reminders}).eq("user_id", user_id).execute()
    _push_for_user(user_id)
    return {"status": "deleted"}