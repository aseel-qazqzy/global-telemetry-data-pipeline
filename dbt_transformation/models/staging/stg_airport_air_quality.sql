with airport_air_quality as (
    select * from {{source("postgres_raw","raw_airport_air_quality")}}
)

select 
airport_code,
pm2_5::float as pm2_5,
pm10::float as pm10,
no2::float as nitrogen_dioxide,
batch_id,
inserted_at
from airport_air_quality
