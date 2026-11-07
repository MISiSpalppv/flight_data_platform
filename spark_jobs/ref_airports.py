import urllib.request

from pyspark.sql import functions as F

from common import BRONZE_AIRPORTS, SILVER_AIRPORTS, get_spark

SOURCE_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
LOCAL_FILE = "/tmp/airports.csv"


def main():
    urllib.request.urlretrieve(SOURCE_URL, LOCAL_FILE)
    spark = get_spark("ref_airports")

    raw = spark.read.option("header", True).option("multiLine", True).option("escape", '"').csv(f"file://{LOCAL_FILE}")
    raw.withColumn("loaded_at", F.current_timestamp()).write.format("delta").mode("overwrite").option(
        "overwriteSchema", True
    ).save(BRONZE_AIRPORTS)

    airports = (
        spark.read.format("delta").load(BRONZE_AIRPORTS)
        .filter(F.col("type").isin("large_airport", "medium_airport") & F.col("iata_code").isNotNull())
        .select(
            F.col("iata_code").alias("iata"),
            F.col("ident").alias("icao"),
            "name",
            F.col("type").alias("airport_type"),
            F.col("municipality").alias("city"),
            F.col("iso_country").alias("country"),
            F.col("continent"),
            F.col("latitude_deg").cast("double").alias("lat"),
            F.col("longitude_deg").cast("double").alias("lon"),
            F.col("elevation_ft").cast("double").alias("elevation_ft"),
        )
    )
    airports.write.format("delta").mode("overwrite").option("overwriteSchema", True).save(SILVER_AIRPORTS)
    print("ref_airports: аэропортов в silver:", airports.count())
    spark.stop()


if __name__ == "__main__":
    main()
