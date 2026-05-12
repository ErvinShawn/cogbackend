from pydantic import BaseModel
from typing import Optional,List
# ---------- AUTH ----------

class UserSignup(BaseModel):
    patient_name: str
    email: str
    password: str
    medical_condition: str
    emergency_contact: str
    profile_photo_url: str

class UserSignin(BaseModel):
    email: str
    password: str

# ---------- GEOFENCE ----------

class Geofence(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    radius_meters: float

# ---------- ROUTINES ----------

# This represents a single step within a routine
# class RoutineStepSchema(BaseModel):
#     title: str
#     description: Optional[str] = None
#     time: str

# class RoutineCreate(BaseModel):
#     device_id: str
#     patient_id: int
#     step: RoutineStepSchema

# class RoutineStepCreate(BaseModel):
#     routine_id: int
#     title: str
#     description: Optional[str] = None
#     time: str

# ---------- ROUTINES (JSONB VERSION) ----------

class ReminderSchema(BaseModel):
    title: str
    description: Optional[str] = None
    time: str

class RoutineUpdate(BaseModel):
    device_id: str
    user_id: int
    reminder: ReminderSchema

# ------Device---
class DeviceCreate(BaseModel):
    device_id: str
    user_id: int 

class DeviceUpdate(BaseModel):
    status: Optional[str] = None
    battery_level: Optional[int] = None
    is_active: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    face_detection: Optional[bool] = None
    object_detection: Optional[bool] = None


# ---------- ALERTS ----------

class DeviceAlertCreate(BaseModel):
    device_id: str
    alert_type: str
    timestamp: Optional[str] = None
    title: Optional[str] = None
    severity: Optional[str] = None