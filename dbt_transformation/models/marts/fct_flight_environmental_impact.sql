-- Final Analytical Mart Template for spatial proximity tracking 
WITH flights as (
    SELECT * FROM {{ref("stg_flight_telemetry")}}
), 

air_quality as (
    SELECT * FROM {{ref("stg_airport_air_quality")}}
),
calculated_proximity as(
    SELECT 
    f.batch_id,
    f.inserted_at as flight_snapshot_time,
    f.aircraft_id,
    a.airport_code,
    f.flight_callsign,
    f.latitude as flight_latitude,
    f.longitude as flight_longitude,
    f.altitude as flight_altitude_meters,
    f.velocity as flight_velocity_ms,
    a.pm2_5,
    a.pm10,
    a.nitrogen_dioxide,
    sqrt(power(f.latitude - 50.0379, 2) + power(f.longitude - 8.5622, 2)) as distance_score

    FROM flights f
    INNER JOIN air_quality a
        ON a.batch_id = f.batch_id

)

SELECT 
    batch_id,
    flight_snapshot_time,
    aircraft_id,
    airport_code,
    flight_callsign,
    flight_latitude,
    flight_longitude,
    flight_altitude_meters,
    flight_velocity_ms,
    pm2_5,
    pm10,
    nitrogen_dioxide,
    ROUND(distance_score::NUMERIC, 4) as distance_score
FROM calculated_proximity
WHERE distance_score <= 15.0
ORDER BY 1 ASC 