# Receiver.py
import os, json, socket, signal, sys, logging
from datetime import datetime, timezone
from pathlib import Path
import argparse

# ---------- Config (no hardcoded paths) ----------
DEF_BASE = Path("./data").resolve()
ENV_BASE = Path(os.getenv("FLIGHTSTREAM_DIR", DEF_BASE)).expanduser().resolve()
DEF_REALTIME = ENV_BASE / "flight_realtime.json"
DEF_LOG_DIR = ENV_BASE / "logs"

# CLI
parser = argparse.ArgumentParser(description="FlightStream UDP receiver")
parser.add_argument("--realtime", default=os.getenv("FLIGHTSTREAM_REALTIME", str(DEF_REALTIME)),
                    help="Path to realtime JSON (default: ./data/flight_realtime.json)")
parser.add_argument("--log-dir", default=os.getenv("FLIGHTSTREAM_LOG_DIR", str(DEF_LOG_DIR)),
                    help="Directory for rolling logs (default: ./data/logs)")
parser.add_argument("--bind-ip", default=os.getenv("FLIGHT_UDP_IP", "0.0.0.0"),
                    help="Bind IP for UDP (default: 0.0.0.0)")
parser.add_argument("--port", type=int, default=int(os.getenv("FLIGHT_UDP_PORT", "9000")),
                    help="UDP port (default: 9000)")
args = parser.parse_args()

REALTIME_PATH = Path(args.realtime).expanduser().resolve()
LOG_DIR = Path(args.log_dir).expanduser().resolve()
LOG_DIR.mkdir(parents=True, exist_ok=True)
REALTIME_PATH.parent.mkdir(parents=True, exist_ok=True)

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOG_PATH = LOG_DIR / f"flight_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# ---------- Helpers ----------
flight_log = []

def num(x, prec):
    return x if (x in (None, "N/A")) else (round(x, prec) if isinstance(x, (int, float)) else x)

def save_all_and_exit(*_):
    LOG_PATH.write_text(json.dumps(flight_log, indent=2))
    logging.info("Saved %d entries to %s", len(flight_log), LOG_PATH)
    sys.exit(0)

# ---------- Main ----------
def main():
    signal.signal(signal.SIGINT, save_all_and_exit)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.bind_ip, args.port))
    logging.info("Listening on %s:%d", args.bind_ip, args.port)
    logging.info("Realtime -> %s", REALTIME_PATH)
    logging.info("Logs     -> %s", LOG_DIR)

    while True:
        raw, _ = sock.recvfrom(4096)
        data = json.loads(raw)

        # Expect normalized keys from Source.py (altitude_ft, speed_knots, etc.)【turn2file0†source】
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "altitude_ft": num(data.get("altitude_ft"), 4),
            "speed_knots": num(data.get("speed_knots"), 4),
            "verticalspeed_fpm": num(data.get("verticalspeed_fpm"), 4),
            "lat": num(data.get("lat"), 4),
            "lon": num(data.get("lon"), 4),
            "heading_deg": num(data.get("heading_deg"), 4),
            "fuel_amount_gallons": num(data.get("fuel_amount_gallons"), 2),
            "fuel_percent_remaining": num(data.get("fuel_percent_remaining"), 2),
            "wind_velocity_knots": num(data.get("wind_velocity_knots"), 4),
            "wind_direction_deg": num(data.get("wind_direction_deg"), 4),
            "temperature_c": num(data.get("temperature_c"), 4),
            "weather_pressure_inHg": num(data.get("weather_pressure_inHg"), 4),
            "time_to_dest_minutes": num(data.get("time_to_dest_minutes"), 2),
            "takeoff_airport": data.get("takeoff_airport"),
            "next_waypoint": data.get("next_waypoint"),
            "wp_distance_meters": num(data.get("wp_distance_meters"), 2),
            "metar_active_wp": data.get("metar_active_wp"),
            "metar_takeoff_wp": data.get("metar_takeoff_wp"),
        }

        flight_log.append(entry)
        REALTIME_PATH.write_text(json.dumps(entry, indent=2))
        LOG_PATH.write_text(json.dumps(flight_log, indent=2))

if __name__ == "__main__":
    main()
