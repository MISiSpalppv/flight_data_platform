from delta.tables import DeltaTable
from pyspark.sql import Window
from pyspark.sql import functions as F

from common import GOLD, SILVER_AIRPORTS, SILVER_FLIGHTS, get_spark


def save(df, name):
    df.write.format("delta").mode("overwrite").option("overwriteSchema", True).save(f"{GOLD}/{name}")
    print(f"gold.{name}: {df.count()} строк")


def live_aircraft(pos):
    latest_ts = pos.agg(F.max("position_ts")).first()[0]
    recent = pos.filter(F.col("position_ts") >= F.lit(latest_ts) - F.expr("INTERVAL 10 MINUTES"))
    w = Window.partitionBy("icao24").orderBy(F.col("position_ts").desc())
    return (
        recent.withColumn("rn", F.row_number().over(w))
        .filter("rn = 1")
        .select(
            "icao24", "callsign", "registration", "aircraft_type", "operator", "region",
            "lat", "lon", "altitude_ft", "speed_kt", "heading_deg", "vertical_rate_fpm",
            "on_ground", "position_ts",
        )
    )


def traffic_by_region_hour(pos):
    return (
        pos.groupBy("region", F.date_trunc("hour", "position_ts").alias("hour"))
        .agg(
            F.countDistinct("icao24").alias("unique_aircraft"),
            F.count("*").alias("position_reports"),
            F.round(F.avg(F.when(~F.col("on_ground"), F.col("altitude_ft"))), 0).alias("avg_altitude_ft"),
            F.round(F.avg(F.when(~F.col("on_ground"), F.col("speed_kt"))), 1).alias("avg_speed_kt"),
            F.sum(F.col("on_ground").cast("int")).alias("on_ground_reports"),
        )
    )


def airline_activity(pos):
    with_airline = pos.withColumn("airline_code", F.regexp_extract("callsign", r"^([A-Z]{3})\d", 1)).filter(
        F.col("airline_code") != ""
    )
    return (
        with_airline.groupBy("position_date", "airline_code")
        .agg(
            F.countDistinct("icao24").alias("unique_aircraft"),
            F.countDistinct("callsign").alias("unique_flights"),
            F.round(F.avg(F.when(~F.col("on_ground"), F.col("speed_kt"))), 1).alias("avg_speed_kt"),
            F.round(F.avg(F.when(~F.col("on_ground"), F.col("altitude_ft"))), 0).alias("avg_altitude_ft"),
            F.max("altitude_ft").alias("max_altitude_ft"),
        )
    )


def aircraft_types(pos):
    return (
        pos.filter(F.col("aircraft_type").isNotNull())
        .groupBy("aircraft_type")
        .agg(
            F.first("aircraft_desc", ignorenulls=True).alias("aircraft_desc"),
            F.countDistinct("icao24").alias("unique_aircraft"),
            F.count("*").alias("position_reports"),
            F.round(F.avg(F.when(~F.col("on_ground"), F.col("speed_kt"))), 1).alias("avg_speed_kt"),
            F.max("altitude_ft").alias("max_altitude_ft"),
            F.max("speed_kt").alias("max_speed_kt"),
        )
    )


def aircraft_daily(pos):
    return (
        pos.groupBy("position_date", "icao24")
        .agg(
            F.first("callsign", ignorenulls=True).alias("callsign"),
            F.first("registration", ignorenulls=True).alias("registration"),
            F.first("aircraft_type", ignorenulls=True).alias("aircraft_type"),
            F.min("position_ts").alias("first_seen"),
            F.max("position_ts").alias("last_seen"),
            F.count("*").alias("position_reports"),
            F.max("altitude_ft").alias("max_altitude_ft"),
            F.max("speed_kt").alias("max_speed_kt"),
            F.countDistinct("region").alias("regions_visited"),
        )
    )


def emergency_events(pos):
    return (
        pos.filter(
            F.col("emergency").isin("general", "nordo", "unlawful", "downed", "minfuel")
            | F.col("squawk").isin("7500", "7600", "7700")
        )
        .select(
            "position_ts", "icao24", "callsign", "registration", "aircraft_type", "region",
            "squawk", "emergency", "lat", "lon", "altitude_ft", "speed_kt",
        )
        .withColumn(
            "reason",
            F.when(F.col("squawk") == "7500", "hijack")
            .when(F.col("squawk") == "7600", "radio_failure")
            .when(F.col("squawk") == "7700", "general_emergency")
            .otherwise(F.col("emergency")),
        )
    )


def airport_activity(pos, airports):
    low = pos.filter(F.col("on_ground") | (F.col("altitude_ft") < 4000)).select(
        "icao24", "callsign", "position_ts", "lat", "lon", "altitude_ft", "on_ground", "vertical_rate_fpm"
    )
    ap = F.broadcast(airports.select("iata", "name", "city", "country", F.col("lat").alias("ap_lat"), F.col("lon").alias("ap_lon")))
    cond = (F.abs(low.lat - F.col("ap_lat")) < 0.15) & (F.abs(low.lon - F.col("ap_lon")) < 0.25)
    joined = low.join(ap, cond)

    dlat = F.radians(F.col("lat") - F.col("ap_lat"))
    dlon = F.radians(F.col("lon") - F.col("ap_lon"))
    a = F.sin(dlat / 2) ** 2 + F.cos(F.radians("lat")) * F.cos(F.radians("ap_lat")) * F.sin(dlon / 2) ** 2
    near = joined.withColumn("distance_km", 12742 * F.asin(F.sqrt(a))).filter("distance_km <= 12")

    return (
        near.groupBy("iata", "name", "city", "country", F.date_trunc("hour", "position_ts").alias("hour"))
        .agg(
            F.countDistinct("icao24").alias("unique_aircraft"),
            F.countDistinct(F.when(F.col("on_ground"), F.col("icao24"))).alias("aircraft_on_ground"),
            F.countDistinct(F.when(~F.col("on_ground") & (F.col("vertical_rate_fpm") < -300), F.col("icao24"))).alias("arriving_aircraft"),
            F.countDistinct(F.when(~F.col("on_ground") & (F.col("vertical_rate_fpm") > 300), F.col("icao24"))).alias("departing_aircraft"),
        )
    )


def main():
    spark = get_spark("gold_marts")
    pos = spark.read.format("delta").load(SILVER_FLIGHTS).cache()

    save(live_aircraft(pos), "mart_live_aircraft")
    save(traffic_by_region_hour(pos), "mart_traffic_region_hour")
    save(airline_activity(pos), "mart_airline_activity")
    save(aircraft_types(pos), "mart_aircraft_types")
    save(aircraft_daily(pos), "mart_aircraft_daily")
    save(emergency_events(pos), "mart_emergency_events")

    if DeltaTable.isDeltaTable(spark, SILVER_AIRPORTS):
        airports = spark.read.format("delta").load(SILVER_AIRPORTS)
        save(airport_activity(pos, airports), "mart_airport_activity")
    else:
        print("справочник аэропортов ещё не загружен, mart_airport_activity пропущена")

    spark.stop()


if __name__ == "__main__":
    main()
