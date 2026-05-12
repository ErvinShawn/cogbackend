from fastapi import APIRouter, HTTPException
from src.db import supabase
from pydantic import BaseModel
from typing import Optional


class ReminderSchema(BaseModel):
    title: str
    description: Optional[str] = None
    time: str

class RoutineUpdate(BaseModel):
    device_id: str
    user_id: int
    reminder: ReminderSchema
router = APIRouter(prefix="/routines", tags=["Routines"])

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

        reminders.append(
            {
                "title": data.reminder.title,
                "description": data.reminder.description,
                "time": data.reminder.time,
            }
        )

        supabase.table("routines").upsert(
            {"device_id": data.device_id, "user_id": data.user_id, "reminders": reminders},
            on_conflict="user_id",
        ).execute()
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