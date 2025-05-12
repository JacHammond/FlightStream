from typing import List
from pydantic import BaseModel
import requests
from datetime import datetime
import json
import re
import os


class Pipeline:
    # Define a Pydantic model to store configuration values
    class Valves(BaseModel):
        # Paths to various important files
        file_path: str = "/home/jacob/Desktop/MSFS-FlightData/flight_realtime.json"  # Path to the real-time flight telemetry JSON
        labeled_output_path: str = "/home/jacob/Desktop/MSFS-FlightData/labeled_output.json"  # Path to labeled telemetry data
        labeling_policy_path: str = "/home/jacob/Desktop/MSFS-FlightData/Labeling/labeling_policy.json"  # Path to the labeling policy JSON
        ollama_url: str = "http://localhost:11434"  # Local server URL for Ollama API
        model_name: str = "llama3"  # Model name used for AI queries
        plane_model: str = "Enter Aircraft Model Here"  # Placeholder for aircraft model name

    def __init__(self):
        # Initialize the Valves configuration and load telemetry data
        self.valves = self.Valves()
        self.telemetry_data = ""  # Placeholder for raw telemetry data
        self.load_telemetry_data()  # Populate telemetry data on initialization

    def load_telemetry_data(self):
        """
        Loads the flight telemetry data from the specified JSON file into memory.
        If an error occurs, the telemetry data will contain the error message.
        """
        try:
            with open(self.valves.file_path, "r") as f:
                # Strip whitespace and join lines to maintain formatting
                self.telemetry_data = "\n".join([line.strip() for line in f if line.strip()])
        except Exception as e:
            # If an error occurs during file read, store the error message
            self.telemetry_data = f"Error reading file: {e}"

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> str:
        """
        Main pipeline method to handle user queries.
        Routes the query to either a labeling-focused response or a standard telemetry-based response.
        """

        # Check if the user message is related to data labeling
        if any(q in user_message.lower() for q in ["data label", "labeling", "label data:", "why is it labeled", "explain label"]):
            try:
                # Attempt to load labeled data from the specified path
                with open(self.valves.labeled_output_path, "r") as f:
                    label_data = json.load(f)
            except Exception as e:
                # If labeled data is not available, return an error message
                return f"No labeled data available yet. Please run 'Label Flight Telemetry' first.\n(Error: {e})"

            # Format the label data for display
            label_context = "\n".join([f"{k}: {v}" for k, v in label_data.items()])

            # Build the prompt for the AI model, providing both telemetry and label data
            prompt = (
                f"You are a flight telemetry and labeling analyst.\n\n"
                f"---\nTelemetry Data:\n{self.telemetry_data}\n"
                f"---\nLabel Data:\n{label_context}\n"
                f"---\nUser Question: {user_message}\n\n"
                f"Use both the telemetry and label data to explain why the label was assigned. "
                f"If there's not enough information to explain the label, say so explicitly."
            )

            # Send the prompt to the Ollama API and get a response
            try:
                response = requests.post(
                    f"{self.valves.ollama_url}/api/generate",
                    json={
                        "model": self.valves.model_name,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()  # Ensure the request succeeded
                return response.json()["response"].strip()
            except Exception as e:
                return f"Ollama error while answering label query: {e}"

        # If not labeling-related, proceed with normal telemetry reasoning
        try:
            # Load fresh telemetry data
            with open(self.valves.file_path, "r") as f:
                self.telemetry_data = "\n".join([line.strip() for line in f if line.strip()])
        except Exception as e:
            # Handle file reading errors
            return f"Error reading telemetry: {e}"

        # If the telemetry data is empty or contains an error, return it
        if not self.telemetry_data or self.telemetry_data.startswith("Error"):
            return self.telemetry_data

        # Get the current UTC timestamp for context
        current_utc_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Construct the prompt for the AI model for general telemetry analysis
        prompt = (
            f"You are an AI Co-Pilot helping interpret flight telemetry for a {self.valves.plane_model} recorded at {current_utc_time}.\n"
            f"Based on this telemetry data:\n\n"
            f"{self.telemetry_data}\n\n"
            f"Answer the user's question:\n{user_message}"
        )

        # Send the constructed prompt to the Ollama API for processing
        try:
            response = requests.post(
                f"{self.valves.ollama_url}/api/generate",
                json={
                    "model": self.valves.model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()  # Ensure the request was successful
            return response.json()["response"].strip()
        except Exception as e:
            # Handle any errors during API interaction
            return f"Ollama error: {e}"
