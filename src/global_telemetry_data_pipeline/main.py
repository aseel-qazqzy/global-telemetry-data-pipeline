import requests
import pandas as pd
import uuid
from datetime import datetime, timezone
import logging
from pathlib import Path

from src.global_telemetry_data_pipeline import database

# Configure the root logging layout 
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/pipeline.log", mode="a")
    ]
)

logger = logging.getLogger(__name__)

def fetch_air_quality(lat: float, lon: float, airport_code: str) -> dict:
    """
    Args:
        lat (float): The target latitude of the airport hub.
        lon (float): The target longitude of the airport hub.
        airport (string): The airport code
    Returns:
        dict: A structured dictionary containing parsed key matching 
            our target data contract
    """
    query_params = {'latitude':lat, 'longitude':lon, 'current':'pm2_5,pm10,nitrogen_dioxide'}
    api_url = "https://air-quality-api.open-meteo.com/v1/air-quality"

    try:
        response = requests.get(api_url, params=query_params)
        response.raise_for_status() # Automatically triggers exception if status code is 4xx or 5xx
        payload = response.json()
        current_data = payload.get("current", {})
        parsed_record = {
            "airport_code":airport_code,
            "pm2_5":current_data.get("pm2_5"),
            "pm10":current_data.get("pm10"),
            "no2":current_data.get("nitrogen_dioxide")
        }
        return parsed_record
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to extract air quality data from endpoint: {e}")
        return {}


def fetch_flight_telemetry() -> list[dict]:
    """
    Extracts real-time state vectors of global flights currently in transit.
    Returns:
        list[dict]: A clean list of inner flight dicts 
    """

    url = "https://opensky-network.org/api/states/all"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        payload = response.json()
        raw_states = payload.get("states", {})
        parsed_flights = []
        
        if not raw_states:
            return parsed_flights
        
        for row in raw_states[:15]:
            if row[5] is None or row[6] is None:
                continue
            
            flight_record = {
                "icao24": row[0],
                "callsign": row[1].strip() if row[1] else None,
                "longitude": float(row[5]) if row[5] is not None else None,
                "latitude": float(row[6]) if row[6] is not None else None,
                "altitude": float(row[7]) if row[7] is not None else None,
                "velocity": float(row[9]) if row[9] is not None else None
            }
            parsed_flights.append(flight_record)
        return parsed_flights
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to extract flight telemetry data: {e}")
        return []

def run_ingestion_pipeline() -> None:
    """
    The execution engine driver that orchestrates the extraction batch run.
    steps:
    1. Initialise database tables
    2. Validate database contract tables inside the PostgreSQL
    3. Invokes the API extraction drivers to pull parsed. structured payloads.
    """
    run_batch_id = str(uuid.uuid4()) # Added execution parentheses fix!
    run_timestamp = datetime.now(timezone.utc)
    
    logger.info(f"Kicking off data ingestion job batch: {run_batch_id} at {run_timestamp}")
    
    # Step A: Validate table structures exist inside Postgres
    database.init_raw_tables()
    
    # Step B: Trigger Extraction Drivers 
    logger.info("Extracting live weather metrics for FRA airport...")
    air_metrics = fetch_air_quality(50.0379, 8.5622, "FRA")
    logger.info(f"Extracted Air Data: {air_metrics}")
    
    # Step C: Trigger Extraction of 
    logger.info("Extracting Flight telemetry Data...")
    flight_telemetry = fetch_flight_telemetry()
    logger.info(f"Extracted Flight telemetry Data")
    
    # Step D: insert into raw_airport_air_quality table
    logger.info("Insert data to raw_airport_air_quality .. ")
    database.insert_air_quality(air_metrics, run_batch_id, run_timestamp)
    logger.info("Data is inserted to the table..")
    
    # Step E: insert into raw_flight_telemetry table
    logger.info("Insert data to raw_flight_telemetry .. ")
    database.insert_flight_telemetry(flight_telemetry, run_batch_id, run_timestamp)
    logger.info("Data is inserted to the table..")
def main() -> None:
    print("It works. Now build something.")


if __name__ == "__main__":
    run_ingestion_pipeline()
