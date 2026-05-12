from fastapi import APIRouter, HTTPException
from src.db import supabase
from pydantic import BaseModel

router = APIRouter(prefix="/faces", tags=["Faces"])


# ---------- MODEL ----------
class FaceCreate(BaseModel):
    person_name: str
    relationship: str
    image_url: str


# ---------- CREATE FACE ----------
@router.post("")
def create_face(data: FaceCreate):
    try:
        response = supabase.table("faces").insert(data.model_dump()).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to save face")

        face_id = response.data[0].get("id")

        return {
            "message": "face saved",
            "id": face_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- GET ALL ----------
@router.get("")
def get_faces():
    response = supabase.table("faces").select("*").order("id", desc=True).execute()
    return response.data or []


# ---------- DELETE FACE ----------
@router.delete("/{face_id}")
def delete_face(face_id: int):
    response = supabase.table("faces").delete().eq("id", face_id).execute()
    deleted = response.data[0] if response.data else None

    if not deleted:
        raise HTTPException(status_code=404, detail="Face not found")

    return {"message": "face deleted"}