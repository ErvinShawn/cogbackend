from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import faces, routines, geofence, auth, devices, alerts, events
from src.db import supabase


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def test_db_connection():
    try:
        supabase.table("users").select("id").limit(1).execute()
        print("DATABASE CONNECTED SUCCESSFULLY")


    except Exception as e:
        print("DATABASE CONNECTION FAILED")
        print(e)

app.include_router(faces.router)
app.include_router(routines.router)
app.include_router(geofence.router)
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(alerts.router)
app.include_router(events.router)