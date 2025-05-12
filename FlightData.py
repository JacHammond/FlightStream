import socket
import json
from datetime import datetime, timezone
import os
import signal
import sys
import glob

SAVE_DIR = os.path.expanduser("~/Desktop/MSFS-FlightData/Logs")
os.makedirs(SAVE_DIR, exist_ok=True)

REALTIME_PATH = os.path.expanduser("~/Desktop/MSFS-FlightData/flight_realtime.json")

def get_next_log_path():
    existing = glob.glob(os.path.join(SAVE_DIR, "flight_log*.json"))
    nums = [int(f.split("flight_log")[-1].split(".json")[0]) for f in existing if f.split("flight_log")[-1].split(".json")[0].isdigit()]
    next_num = max(nums, default=0) + 1
    return os.path.join(SAVE_DIR, f"flight_log{next_num}.json")

LOG_PATH = get_next_log_path()
flight_log = []

def process_value(value, precision):
    if value is None or value == "N/A":
        return value
    if not isinstance(value, (int, float)):
        return value
    return round(value, precision)

def save_realtime(entry):
    with open(REALTIME_PATH, "w") as f:
        json.dump(entry, f, indent=2)

def save_flight_log():
    with open(LOG_PATH, "w") as f:
        json.dump(flight_log, f, indent=2)  # Save the entire flight log to the saved log file

def save_and_exit(signum, frame):
    with open(LOG_PATH, "w") as f:
        json.dump(flight_log, f, indent=2)
    print(f"\nSaved {len(flight_log)} entries to {LOG_PATH}")
    sys.exit(0)

signal.signal(signal.SIGINT, save_and_exit)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9000))

print(f"Listening for flight data... Saving to {LOG_PATH}. Press Ctrl+C to stop.\n")

while True:
    raw, addr = sock.recvfrom(4096)
    data = json.loads(raw)

    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "altitude_ft": process_value(data.get("altitude"), 4),
        "speed_knots": process_value(data.get("airspeed"), 4),
        "verticalspeed_fpm": process_value(data.get("vertical_speed"), 4),
        "lat": process_value(data.get("latitude"), 4),
        "lon": process_value(data.get("longitude"), 4),
        "heading_deg": process_value(data.get("heading"), 4),
        "fuel_ammount_gallons": process_value(data.get("fuel_quantity"), 4),
        "feul_percent_remaining": process_value(data.get("fuel_percent_remaining"), 4),
        "wind_velocity_knots": process_value(data.get("wind_velocity"), 4),
        "wind_direction_deg": process_value(data.get("wind_direction"), 4),
        "temperature C°": process_value(data.get("weather_temperature"), 4),
        "weather_pressure_inHg": process_value(data.get("weather_pressure"), 4),
        "time_to_dest_minutes": process_value(data.get("time_enroute"), 2),
        "takeoff_airport": process_value(data.get("flight_plan_takeoff"), 4),
        "next_waypoint": data.get("flight_plan_active_wp"),
        "wp_distance_meters": process_value(data.get("flight_plan_distance"), 2),
        "wind_velocity": process_value(data.get("wind_velocity"), 4),
        "wind_direction": process_value(data.get("wind_direction"), 4),
        "Active METAR": process_value(data.get("metar_active_wp"), 4),
        "Takeoff METAR": process_value(data.get("metar_takeoff_wp"), 4),
                }

    flight_log.append(entry)
    save_realtime(entry)  # Save the latest entry to the realtime file
    save_flight_log()  # Save the entire log to the saved log file
    #print(f"Captured: {entry}")
