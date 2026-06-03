# faces.py
from fastapi import APIRouter, HTTPException
from src.db import supabase
from src.routers.events import push_event
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/faces", tags=["Faces"])

class FaceCreate(BaseModel):
    person_name: str
    relationship: str
    image_urls: List[str]
    user_id: int

class FaceUpdate(BaseModel):
    person_name: Optional[str] = None
    relationship: Optional[str] = None
    image_urls: Optional[List[str]] = None

def _push_for_user(user_id: int):
    device = supabase.table("devices").select("device_id").eq("user_id", user_id).execute()
    for d in (device.data or []):
        push_event(d["device_id"], "faces_updated")

@router.post("")
def create_face(data: FaceCreate):
    try:
        response = supabase.table("faces").insert(data.model_dump()).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to save face")
        _push_for_user(data.user_id)
        return {"message": "face saved", "id": response.data[0].get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")
def get_faces(user_id: int):
    response = (
        supabase.table("faces")
        .select("*")
        .eq("user_id", user_id)
        .order("id", desc=True)
        .execute()
    )
    return response.data or []

@router.patch("/{face_id}")
def update_face(face_id: int, data: FaceUpdate):
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    response = supabase.table("faces").update(update_data).eq("id", face_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Face not found")
    face = supabase.table("faces").select("user_id").eq("id", face_id).limit(1).execute()
    if face.data:
        _push_for_user(face.data[0]["user_id"])
    return {"message": "face updated"}

@router.delete("/{face_id}")
def delete_face(face_id: int):
    face = supabase.table("faces").select("user_id").eq("id", face_id).limit(1).execute()
    response = supabase.table("faces").delete().eq("id", face_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Face not found")
    if face.data:
        _push_for_user(face.data[0]["user_id"])
    return {"message": "face deleted"}