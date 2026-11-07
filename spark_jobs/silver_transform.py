from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql import types as T

from common import BRONZE_FLIGHTS, CHECKPOINTS, SILVER_FLIGHTS, get_spark

EVENT_SCHEMA = T.StructType([
    T.StructField("hex", T.StringType()),
    T.StructField("flight", T.StringType()),
    T.StructField("r", T.StringType()),
    T.StructField("t", T.StringType()),
    T.StructField("desc", T.StringType()),
    T.StructField("ownOp", T.StringType()),
    T.StructField("category", T.StringType()),
    T.StructField("squawk", T.StringType()),
    T.StructField("emergency", T.StringType()),
    T.StructField("lat", T.DoubleType()),
    T.StructField("lon", T.DoubleType()),
    T.StructField("alt_baro", T.StringType()),
    T.StructField("alt_geom", T.DoubleType()),
    T.StructField("gs", T.DoubleType()),
    T.StructField("track", T.DoubleType()),
    T.StructField("baro_rate", T.DoubleType()),
    T.StructField("seen_pos", T.DoubleType()),
    T.StructField("region", T.StringType()),
    T.StructField("api_ts_ms", T.LongType()),
    T.StructField("ingest_ts", T.StringType()),
])


def transform(df):
    parsed = df.select(F.from_json("payload", EVENT_SCHEMA).alias("e"), "kafka_ts").select("e.*", "kafka_ts")

    on_ground = F.coalesce(F.col("alt_baro") == "ground", F.lit(False))
    alt_ft = F.when(on_ground, F.lit(0)).otherwise(F.col("alt_baro").cast("double"))
    position_ts = F.to_timestamp(
        F.from_unixtime(F.col("api_ts_ms") / 1000 - F.coalesce(F.col("seen_pos"), F.lit(0.0)))
    )

    return (
        parsed.select(
            F.col("hex").alias("icao24"),
            F.upper(F.trim("flight")).alias("callsign"),
            F.col("r").alias("registration"),
            F.col("t").alias("aircraft_type"),
            F.col("desc").alias("aircraft_desc"),
            F.col("ownOp").alias("operator"),
            "category",
            "squawk",
            F.coalesce("emergency", F.lit("none")).alias("emergency"),
            "lat",
            "lon",
            alt_ft.alias("altitude_ft"),
            F.col("alt_geom").alias("altitude_geom_ft"),
            F.col("gs").alias("speed_kt"),
            F.col("track").alias("heading_deg"),
            F.col("baro_rate").alias("vertical_rate_fpm"),
            on_ground.alias("on_ground"),
            "region",
            position_ts.alias("position_ts"),
            "kafka_ts",
        )
        .filter(F.col("icao24").isNotNull() & F.col("position_ts").isNotNull())
        .filter(F.col("lat").between(-90, 90) & F.col("lon").between(-180, 180))
        .filter(F.col("speed_kt").isNull() | (F.col("speed_kt") < 1500))
        .filter(F.col("altitude_ft").isNull() | F.col("altitude_ft").between(-1500, 65000))
        .withColumn("position_date", F.to_date("position_ts"))
        .dropDuplicates(["icao24", "position_ts"])
    )


def upsert_batch(batch_df, batch_id):
    clean = transform(batch_df)
    spark = batch_df.sparkSession
    if not DeltaTable.isDeltaTable(spark, SILVER_FLIGHTS):
        clean.write.format("delta").partitionBy("position_date").save(SILVER_FLIGHTS)
        return
    target = DeltaTable.forPath(spark, SILVER_FLIGHTS)
    (
        target.alias("t")
        .merge(clean.alias("s"), "t.icao24 = s.icao24 AND t.position_ts = s.position_ts AND t.position_date = s.position_date")
        .whenNotMatchedInsertAll()
        .execute()
    )


def main():
    spark = get_spark("silver_transform")
    stream = spark.readStream.format("delta").option("maxFilesPerTrigger", 200).load(BRONZE_FLIGHTS)
    query = (
        stream.writeStream.foreachBatch(upsert_batch)
        .option("checkpointLocation", f"{CHECKPOINTS}/silver_flights")
        .trigger(availableNow=True)
        .start()
    )
    query.awaitTermination()
    spark.stop()


if __name__ == "__main__":
    main()
