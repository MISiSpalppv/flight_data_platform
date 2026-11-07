from pyspark.sql import functions as F

from common import BRONZE_FLIGHTS, CHECKPOINTS, KAFKA_BOOTSTRAP, TOPIC, get_spark


def main():
    spark = get_spark("bronze_ingest")

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "earliest")
        .option("maxOffsetsPerTrigger", 400000)
        .option("failOnDataLoss", "false")
        .load()
    )

    bronze = raw.select(
        F.col("key").cast("string").alias("kafka_key"),
        F.col("value").cast("string").alias("payload"),
        F.col("topic").alias("kafka_topic"),
        F.col("partition").alias("kafka_partition"),
        F.col("offset").alias("kafka_offset"),
        F.col("timestamp").alias("kafka_ts"),
        F.current_timestamp().alias("bronze_loaded_at"),
    ).withColumn("ingest_date", F.to_date("kafka_ts"))

    query = (
        bronze.writeStream.format("delta")
        .outputMode("append")
        .option("checkpointLocation", f"{CHECKPOINTS}/bronze_flights")
        .partitionBy("ingest_date")
        .trigger(availableNow=True)
        .start(BRONZE_FLIGHTS)
    )
    query.awaitTermination()
    print("bronze_ingest: обработано строк за запуск:", sum(p.get("numInputRows", 0) for p in query.recentProgress))
    spark.stop()


if __name__ == "__main__":
    main()
