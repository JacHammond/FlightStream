from SimConnect import SimConnect, AircraftRequests
import socket
import json
import time
from avwx import Metar

UDP_IP = "192.168.0.8"  # The IP of the receiver
UDP_PORT = 9000
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Connect to MSFS
sm = SimConnect()
aq = AircraftRequests(sm)

print("Connected to MSFS. Sending flight data...\n")

def safe_decode(value):
    if isinstance(value, bytes):
        return value.decode().strip()
    return value if value is not None else "N/A"

def fetch_metar_data_by_icao(icao):
    """Fetch METAR data using the AVWX library and ICAO code."""
    try:
        metar = Metar(icao)
        if metar.update():
            return metar.raw  # Return the raw METAR string
        else:
            print(f"Failed to fetch METAR for ICAO {icao}")
            return "N/A"
    except Exception as e:
        print(f"Error fetching METAR for ICAO {icao}: {e}")
        return "N/A"

try:
    while True:
        # Collect telemetry
        alt = aq.get("PLANE_ALTITUDE") or "N/A"
        speed = aq.get("AIRSPEED_INDICATED") or "N/A"
        vs = aq.get("VERTICAL_SPEED") or "N/A"
        lat = aq.get("PLANE_LATITUDE") or "N/A"
        lon = aq.get("PLANE_LONGITUDE") or "N/A"
        hdg = aq.get("MAGNETIC_COMPASS") or "N/A"
        fuel_qty = aq.get("FUEL_TOTAL_QUANTITY") or "N/A"  # gallons
        fuel_weight = aq.get("FUEL_TOTAL_WEIGHT") or "N/A"  # pounds
        wind_vel = aq.get("AMBIENT_WIND_VELOCITY") or "N/A"
        wind_dir = aq.get("AMBIENT_WIND_DIRECTION") or "N/A"
        weather_temp = aq.get("AMBIENT_TEMPERATURE") or "N/A"
        weather_pressure = aq.get("AMBIENT_PRESSURE") or "N/A"
        time_enroute = aq.get("GPS_ETE") or "N/A"
        flight_plan_takeoff = safe_decode(aq.get("GPS_WP_PREV_ID"))
        flight_plan_active_wp = safe_decode(aq.get("GPS_WP_NEXT_ID"))
        flight_plan_distance = aq.get("GPS_WP_DISTANCE") or "N/A"
        max_fuel = aq.get("FUEL_TOTAL_CAPACITY") or "N/A"  # gallons

        # Adjust fuel percentage calculation to match in-game values
        if fuel_qty != "N/A" and max_fuel > 0:
            fuel_percent = (fuel_qty / max_fuel) * 100
            fuel_percent = min(max(fuel_percent, 0), 100)  # Clamp value between 0 and 100
        else:
            fuel_percent = "N/A"

        # Convert time_enroute from seconds to minutes
        time_enroute = time_enroute / 60 if time_enroute != "N/A" else "N/A"

        # Fetch METAR for active waypoint and takeoff waypoint
        metar_data_active_wp = {}
        if flight_plan_active_wp != "N/A":
            metar_data_active_wp = fetch_metar_data_by_icao(flight_plan_active_wp)

        metar_data_takeoff_wp = {}
        if flight_plan_takeoff != "N/A":
            metar_data_takeoff_wp = fetch_metar_data_by_icao(flight_plan_takeoff)

        # Build packet
        data = {
            "metar_active_wp": metar_data_active_wp if isinstance(metar_data_active_wp, str) else metar_data_active_wp.get('sanitized', ''),
            "metar_takeoff_wp": metar_data_takeoff_wp if isinstance(metar_data_takeoff_wp, str) else metar_data_takeoff_wp.get('sanitized', ''),
            "altitude": alt if alt == "N/A" else round(alt, 4),
            "airspeed": speed if speed == "N/A" else round(speed, 4),
            "vertical_speed": vs if vs == "N/A" else round(vs, 4),
            "latitude": lat if lat == "N/A" else round(lat, 4),
            "longitude": lon if lon == "N/A" else round(lon, 4),
            "heading": hdg if hdg == "N/A" else round(hdg, 4),
            "fuel_quantity": fuel_qty if fuel_qty == "N/A" else round(fuel_qty, 2),
            "fuel_percent_remaining": fuel_percent if fuel_percent == "N/A" else round(fuel_percent, 2),
            "wind_velocity": wind_vel if wind_vel == "N/A" else round(wind_vel, 4),
            "wind_direction": wind_dir if wind_dir == "N/A" else round(wind_dir, 4),
            "weather_temperature": weather_temp if weather_temp == "N/A" else round(weather_temp, 4),
            "weather_pressure": weather_pressure if weather_pressure == "N/A" else round(weather_pressure, 4),
            "time_enroute": time_enroute if time_enroute == "N/A" else round(time_enroute, 4),
            "flight_plan_takeoff": flight_plan_takeoff,
            "flight_plan_active_wp": flight_plan_active_wp,
            "flight_plan_distance": flight_plan_distance if flight_plan_distance == "N/A" else round(flight_plan_distance, 4)
        }

        # Print to terminal
        print("\nFlight Data:")
        for key, value in data.items():
            if key not in ["metar_active_wp", "metar_takeoff_wp"]:
                print(f"{key}: {value}")
        print(f"\nSanitized METAR Active WP: {data['metar_active_wp']}")
        print(f"Sanitized METAR Takeoff WP: {data['metar_takeoff_wp']}\n")

        # Send UDP packet
        sock.sendto(json.dumps(data).encode(), (UDP_IP, UDP_PORT))

        time.sleep(1)

except KeyboardInterrupt:
    print("\nFlight data streaming stopped.")