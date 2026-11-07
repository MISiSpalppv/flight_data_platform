import os

from pyspark.sql import SparkSession

BUCKET = os.getenv("LAKE_BUCKET", "lakehouse")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "flights.raw")

BRONZE_FLIGHTS = f"s3a://{BUCKET}/bronze/flights_raw"
BRONZE_AIRPORTS = f"s3a://{BUCKET}/bronze/airports_raw"
SILVER_FLIGHTS = f"s3a://{BUCKET}/silver/flight_positions"
SILVER_AIRPORTS = f"s3a://{BUCKET}/silver/airports"
GOLD = f"s3a://{BUCKET}/gold"
CHECKPOINTS = f"s3a://{BUCKET}/_checkpoints"


def get_spark(app_name):
    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[2]")
        .config("spark.driver.memory", os.getenv("SPARK_DRIVER_MEMORY", "1536m"))
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.ui.enabled", "false")
        .config("spark.hadoop.fs.s3a.endpoint", os.environ["S3_ENDPOINT"])
        .config("spark.hadoop.fs.s3a.access.key", os.environ["S3_ACCESS_KEY"])
        .config("spark.hadoop.fs.s3a.secret.key", os.environ["S3_SECRET_KEY"])
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.delta.logStore.class", "org.apache.spark.sql.delta.storage.S3SingleDriverLogStore")
    )
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark
