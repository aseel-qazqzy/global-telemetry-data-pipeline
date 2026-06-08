with flight_telemetry as (
    select * from {{source("postgres_raw","raw_flight_telemetry")}}
)

select 
    icao24 as aircraft_id,
    callsign as flight_callsign,
    latitude::float as latitude,
    longitude::float as longitude,
    velocity::float as velocity,
    altitude::float as altitude,
    batch_id,
    inserted_at
from flight_telemetry
