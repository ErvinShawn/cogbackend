from fastapi import FastAPI
from pydantic import BaseModel
import math

app = FastAPI()


class DeviceAlert(BaseModel):
    device_id: str
    alert_type: str
    timestamp: str

class DeviceLocation(BaseModel):
    device_id: str
    latitude: float
    longitude: float

@app.post("/device/alert")
def receive_alert(alert: DeviceAlert):

    print("ALERT RECEIVED")
    print(alert)

    

    return {
        "status": "alert received",
        "device": alert.device_id
    }


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

@app.post("/geofence/check")
def check_location(location: DeviceLocation):


    distance = calculate_distance(
        location.latitude,
        location.longitude,
        15.2993,
        74.2201
    )

    if distance > 100:
        print("GEOFENCE BREACH")

        return {
            "status": "breach",
            "distance": distance
        }

    return {
        "status": "inside",
        "distance": distance
    }