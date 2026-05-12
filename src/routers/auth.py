from fastapi import APIRouter, HTTPException
from src.db import supabase
from src.models import UserSignup, UserSignin

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup")
def signup(user: UserSignup):
    try:
        payload = user.model_dump()
        payload["email"] = payload["email"].strip().lower()
        response = supabase.table("users").insert(payload).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create user")

        new_user = response.data[0]

        return {
            "message": "user created",
            "user_id": new_user.get("id"),
            "patient_name": new_user.get("patient_name"),
            "medical_condition": new_user.get("medical_condition"),
            "profile_photo_url": new_user.get("profile_photo_url")
        }

    except Exception as e:
        return {"error": str(e)}
    
#signin
@router.post("/signin")
def signin(user: UserSignin):
    normalized_email = user.email.strip().lower()
    response = supabase.table("users").select("*").ilike("email", normalized_email).limit(1).execute()
    result = response.data[0] if response.data else None

    if not result:
        # Backward compatibility for exact raw-email lookups on older records.
        raw_email = user.email.strip()
        if raw_email:
            fallback = supabase.table("users").select("*").eq("email", raw_email).limit(1).execute()
            result = fallback.data[0] if fallback.data else None

    if not result:
        # Legacy compatibility for records that accidentally stored surrounding spaces.
        fuzzy = supabase.table("users").select("*").ilike("email", f"%{normalized_email}%").limit(20).execute()
        for candidate in fuzzy.data or []:
            candidate_email = str(candidate.get("email") or "").strip().lower()
            if candidate_email == normalized_email:
                result = candidate
                break

    if not result:
        raise HTTPException(status_code=401, detail="invalid credentials")

    submitted_password = user.password
    stored_password = result.get("password", "")

    # Backward compatibility for accounts that were saved with surrounding spaces.
    password_matches = (
        submitted_password == stored_password
        or submitted_password.strip() == str(stored_password).strip()
    )

    if not password_matches:
        raise HTTPException(status_code=401, detail="invalid credentials")

    return {
        "message": "login successful",
        "user_id": result["id"],
        "patient_name": result["patient_name"],
        "medical_condition": result["medical_condition"],
        "profile_photo_url": result["profile_photo_url"]
    }