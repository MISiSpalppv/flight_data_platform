FROM apache/airflow:2.10.5-python3.11

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless curl \
    && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

USER airflow
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN SPARK_JARS=$(python -c "import pyspark, os; print(os.path.join(os.path.dirname(pyspark.__file__), 'jars'))") \
    && M=https://repo1.maven.org/maven2 \
    && for u in \
        io/delta/delta-spark_2.12/3.2.1/delta-spark_2.12-3.2.1.jar \
        io/delta/delta-storage/3.2.1/delta-storage-3.2.1.jar \
        org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.3/spark-sql-kafka-0-10_2.12-3.5.3.jar \
        org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.3/spark-token-provider-kafka-0-10_2.12-3.5.3.jar \
        org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar \
        org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar \
        org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar \
        com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar; \
       do curl -fsSL -o "$SPARK_JARS/$(basename $u)" "$M/$u"; done
