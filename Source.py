# Source.py
import os, json, socket, time
from SimConnect import SimConnect, AircraftRequests
from avwx import Metar
import argparse

DestIp = "192.168.0.199"

# Network config
parser = argparse.ArgumentParser(description="FlightStream MSFS source (Running the Game)")
parser.add_argument("--dest-ip", default=os.getenv("FLIGHT_UDP_DEST_IP", DestIp),
                    help="Destination IP (receiver host)")
parser.add_argument("--dest-port", type=int, default=int(os.getenv("FLIGHT_UDP_DEST_PORT", "9000")),
                    help="Destination UDP port")
args = parser.parse_args()

UDP_IP = args.dest_ip
UDP_PORT = args.dest_port

def metar_raw(icao):
    try:
        m = Metar(icao)
        return m.raw if m.update() else "N/A"
    except Exception:
        return "N/A"

def safe_text(v):
    try:
        return v.decode().strip() if isinstance(v, (bytes, bytearray)) else (v if v is not None else "N/A")
    except Exception:
        return "N/A"

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sm = SimConnect()
    aq = AircraftRequests(sm)
    print(f"Connected to MSFS. Streaming to {UDP_IP}:{UDP_PORT} ...")

    while True:
        alt   = aq.get("PLANE_ALTITUDE") or "N/A"
        ias   = aq.get("AIRSPEED_INDICATED") or "N/A"
        vs    = aq.get("VERTICAL_SPEED") or "N/A"
        lat   = aq.get("PLANE_LATITUDE") or "N/A"
        lon   = aq.get("PLANE_LONGITUDE") or "N/A"
        hdg   = aq.get("MAGNETIC_COMPASS") or "N/A"
        qty   = aq.get("FUEL_TOTAL_QUANTITY") or "N/A"
        cap   = aq.get("FUEL_TOTAL_CAPACITY") or "N/A"
        vel   = aq.get("AMBIENT_WIND_VELOCITY") or "N/A"
        wdir  = aq.get("AMBIENT_WIND_DIRECTION") or "N/A"
        temp  = aq.get("AMBIENT_TEMPERATURE") or "N/A"
        pres  = aq.get("AMBIENT_PRESSURE") or "N/A"
        ete   = aq.get("GPS_ETE") or "N/A"
        dep   = safe_text(aq.get("GPS_WP_PREV_ID"))
        nxt   = safe_text(aq.get("GPS_WP_NEXT_ID"))
        dist  = aq.get("GPS_WP_DISTANCE") or "N/A"

        pct = (qty / cap * 100) if (qty != "N/A" and cap not in (0, "N/A")) else "N/A"
        ete_min = (ete / 60) if ete != "N/A" else "N/A"

        pkt = {
            "altitude_ft": alt if alt == "N/A" else round(alt, 4),
            "speed_knots": ias if ias == "N/A" else round(ias, 4),
            "verticalspeed_fpm": vs if vs == "N/A" else round(vs, 4),
            "lat": lat if lat == "N/A" else round(lat, 4),
            "lon": lon if lon == "N/A" else round(lon, 4),
            "heading_deg": hdg if hdg == "N/A" else round(hdg, 4),
            "fuel_amount_gallons": qty if qty == "N/A" else round(qty, 2),
            "fuel_percent_remaining": pct if pct == "N/A" else round(pct, 2),
            "wind_velocity_knots": vel if vel == "N/A" else round(vel, 4),
            "wind_direction_deg": wdir if wdir == "N/A" else round(wdir, 4),
            "temperature_c": temp if temp == "N/A" else round(temp, 4),
            "weather_pressure_inHg": pres if pres == "N/A" else round(pres, 4),
            "time_to_dest_minutes": ete_min if ete_min == "N/A" else round(ete_min, 4),
            "takeoff_airport": dep,
            "next_waypoint": nxt,
            "wp_distance_meters": dist if dist == "N/A" else round(dist, 4),
            "metar_active_wp": metar_raw(nxt) if nxt != "N/A" else "N/A",
            "metar_takeoff_wp": metar_raw(dep) if dep != "N/A" else "N/A",
        }
        sock.sendto(json.dumps(pkt).encode(), (UDP_IP, UDP_PORT))
        time.sleep(1)

if __name__ == "__main__":
    main()
