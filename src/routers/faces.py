from fastapi import APIRouter, HTTPException
from src.db import supabase
from pydantic import BaseModel

router = APIRouter(prefix="/faces", tags=["Faces"])

class FaceCreate(BaseModel):
    person_name: str
    relationship: str
    image_url: str
    user_id: int          

@router.post("")
def create_face(data: FaceCreate):
    try:
        response = supabase.table("faces").insert(data.model_dump()).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to save face")
        return {"message": "face saved", "id": response.data[0].get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")   # scoped to user, not global
def get_faces(user_id: int):
    response = (
        supabase.table("faces")
        .select("*")
        .eq("user_id", user_id)
        .order("id", desc=True)
        .execute()
    )
    return response.data or []

@router.delete("/{face_id}")
def delete_face(face_id: int):
    response = supabase.table("faces").delete().eq("id", face_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Face not found")
    return {"message": "face deleted"}