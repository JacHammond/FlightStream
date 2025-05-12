"""
title: Flight Telemetry Labeler
author: jacob
version: 1.4
required_open_webui_version: 0.3.9
"""

from pydantic import BaseModel
from typing import Optional
import os
import json
import re
import requests
from datetime import datetime


class Action:
    class Valves(BaseModel):
        file_path: str = "/home/jacob/Desktop/MSFS-FlightData/flight_realtime.json"
        output_path: str = "/home/jacob/Desktop/MSFS-FlightData/labeled_output.json"
        labeling_policy_path: str = (
            "/home/jacob/Desktop/MSFS-FlightData/Labeling/labeling_policy.json"
        )
        ollama_url: str = "http://localhost:11434"
        model_name: str = "llama3"

    def __init__(self):
        self.valves = self.Valves()

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Optional[dict]:

        # Load labeling policy
        try:
            with open(self.valves.labeling_policy_path, "r") as f:
                policy = json.load(f)
        except Exception as e:
            return {"content": f"Error loading labeling policy: {e}"}

        # Load telemetry
        try:
            with open(self.valves.file_path, "r") as f:
                telemetry_data = "\n".join([line.strip() for line in f if line.strip()])
        except Exception as e:
            return {"content": f"Error reading telemetry: {e}"}

        # Build instructions from policy rules
        label_instructions = "\n".join(
            [f"- {key}: {desc['rule']}" for key, desc in policy.items()]
        )

        current_utc_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Construct prompt for labeling
        prompt = (
            f"You are a flight telemetry labeling assistant. Based on the following telemetry"
            f"recorded at {current_utc_time}, return a JSON object with these fields:\n"
            f"{label_instructions}\n\n"
            f"Respond ONLY in valid compact JSON format.\n\n"
            f"Telemetry:\n{telemetry_data}"
        )

        # Query Ollama
        try:
            res = requests.post(
                f"{self.valves.ollama_url}/api/generate",
                json={
                    "model": self.valves.model_name,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            res.raise_for_status()
            raw_output = res.json()["response"].strip()
        except Exception as e:
            return {"content": f"Ollama error: {e}"}

        # Extract and parse JSON response
        match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if not match:
            return {"content": f"Failed to extract JSON from response:\n{raw_output}"}

        try:
            label_data = json.loads(match.group(0))
        except Exception as e:
            return {"content": f"JSON parsing error: {e}"}

        # Save output
        try:
            with open(self.valves.output_path, "w") as out:
                json.dump(label_data, out, indent=2)
        except Exception as e:
            return {"content": f"Failed to save labeled output: {e}"}

        # Render table
        header = "\n| Label | Value |\n|-------|--------|\n"
        rows = "\n".join(
            [f"| {key} | {label_data.get(key, 'N/A')} |" for key in policy]
        )
        table = header + rows

        if __event_emitter__:
            await __event_emitter__({"type": "message", "data": {"content": table}})

        return {"content": "Flight telemetry labeled successfully."}
