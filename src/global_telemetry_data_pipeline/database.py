import os
from dotenv import load_dotenv
# db driver adapter used to connect to python applications to a PostgreSQL db
import psycopg2 
import logging

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_db_connection():
    """Establishes a connection to the local PostgreSQL container."""
    conn = None
    db_params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "port": os.getenv("DB_PORT")
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        logger.info("Connection to Docker PostgreSQL..")
    
    except Exception as e:
        logger.exception("Connection Failed", exc_info=True)
    
    return conn

def init_raw_tables():
    """Execute the DDL schemas to create our data tables"""
    table_queries = [
        """
        CREATE TABLE IF NOT EXISTS raw_flight_telemetry ( 
            icao24 VARCHAR(10), 
            callsign VARCHAR(10), 
            latitude NUMERIC(10, 6), 
            longitude NUMERIC(10, 6), 
            velocity FLOAT, 
            altitude FLOAT, 
            batch_id UUID, 
            inserted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (icao24, inserted_at)
        );
        """, 
        """
        CREATE TABLE IF NOT EXISTS raw_airport_air_quality (
            airport_code CHAR(3),
            pm2_5 FLOAT,
            pm10 FLOAT,
            no2 FLOAT,
            batch_id UUID,
            inserted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (airport_code, inserted_at)
        );
        """
    ]

    conn = get_db_connection()
    if conn is None:
        logger.error("No database connection available to initialize tables.")
        return

    cur = None
    try:
        cur = conn.cursor()
        for query in table_queries:
            cur.execute(query)
        conn.commit()  
        logger.info("Database raw data contract tables initialized successfully.")
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error("Failed to execute DDL table initialization definitions", exc_info=True)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def insert_air_quality(record: dict, batch_id: str, run_timestamp) -> None:
    """Insert the data into raw_airport_air_quality table """

    conn = get_db_connection()
    curr = conn.cursor()
    record['batch_id'] = batch_id
    record['run_timestamp'] = run_timestamp
    insert_query = """
    INSERT INTO raw_airport_air_quality(airport_code, pm2_5, pm10, no2, batch_id, inserted_at) 
    values(
        %(airport_code)s, %(pm2_5)s, %(pm10)s, %(no2)s, %(batch_id)s, %(run_timestamp)s
        )
    """
    
    try:
        curr.execute(insert_query, record)
        conn.commit()
        logger.info("Records inserted successfully into raw_airport_air_quality Table")
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error while inserting data to air_quality table: {e}")
        raise # stop execution immediately 
    finally:
        if curr:
            curr.close()
        if conn:
            conn.close()
            
def insert_flight_telemetry(flight_vector: list, batch_id:str, run_timestamp ) -> None:
    "Insert data into raw_flight_telemetry table"
    conn = get_db_connection()
    curr = conn.cursor()
    insert_query = """
    INSERT INTO raw_flight_telemetry(icao24, callsign, longitude, latitude, altitude, velocity, batch_id, inserted_at) 
    VALUES (%(icao24)s, %(callsign)s, %(longitude)s, %(latitude)s, %(altitude)s, %(velocity)s , %(batch_id)s, %(run_timestamp)s)
    """
    try:
        for item in flight_vector:
            item['batch_id'] = batch_id
            item['run_timestamp'] = run_timestamp
            curr.execute(insert_query, item)
        
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error while inserting data to raw_flight_telemetry table: {e}")
        raise
    finally:
        if curr:
            curr.close()
        if conn:
            conn.close()
