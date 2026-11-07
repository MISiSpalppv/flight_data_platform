FROM python:3.11-slim

WORKDIR /app
RUN pip install --no-cache-dir confluent-kafka==2.6.1 requests==2.32.3
COPY producer/producer.py /app/producer.py

CMD ["python", "-u", "producer.py"]
