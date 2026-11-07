import json
import logging
import os
import signal
import time
from datetime import datetime, timezone

import requests
from confluent_kafka import Producer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "flights.raw")
POLL_INTERVAL_SEC = int(os.getenv("POLL_INTERVAL_SEC", "60"))
API_URL = os.getenv("ADSB_API_URL", "https://api.adsb.lol/v2/point/{lat}/{lon}/{radius}")
REQUEST_PAUSE_SEC = 1.5

REGIONS = [
    ("europe_frankfurt", 50.0, 8.5, 250),
    ("europe_london", 51.5, -0.5, 250),
    ("europe_istanbul", 41.0, 28.8, 250),
    ("us_new_york", 40.6, -73.8, 250),
    ("middle_east_dubai", 25.2, 55.3, 250),
    ("asia_singapore", 1.4, 103.9, 250),
]

FIELDS = [
    "hex", "flight", "r", "t", "desc", "ownOp", "category", "squawk", "emergency",
    "lat", "lon", "alt_baro", "alt_geom", "gs", "tas", "mach", "track", "baro_rate",
    "nav_altitude_mcp", "seen", "seen_pos", "rssi", "dst", "dir", "type",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("producer")
running = True


def stop(*_):
    global running
    running = False


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)


def fetch_region(session, lat, lon, radius):
    resp = session.get(API_URL.format(lat=lat, lon=lon, radius=radius), timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("ac", []), payload.get("now")


def main():
    producer = Producer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "linger.ms": 200,
        "compression.type": "lz4",
    })
    session = requests.Session()
    session.headers["User-Agent"] = "flight-data-platform-student-project/1.0"
    log.info("Старт: topic=%s, регионов=%d, интервал=%dс", TOPIC, len(REGIONS), POLL_INTERVAL_SEC)

    while running:
        cycle_start = time.time()
        total = 0
        for name, lat, lon, radius in REGIONS:
            if not running:
                break
            try:
                aircraft, api_now_ms = fetch_region(session, lat, lon, radius)
            except Exception as exc:
                log.warning("Регион %s: ошибка запроса: %s", name, exc)
                time.sleep(REQUEST_PAUSE_SEC)
                continue

            ingest_ts = datetime.now(timezone.utc).isoformat()
            sent = 0
            for ac in aircraft:
                if "hex" not in ac or "lat" not in ac or "lon" not in ac:
                    continue
                event = {k: ac.get(k) for k in FIELDS}
                event["region"] = name
                event["api_ts_ms"] = api_now_ms
                event["ingest_ts"] = ingest_ts
                producer.produce(TOPIC, key=ac["hex"], value=json.dumps(event, ensure_ascii=False))
                sent += 1
            producer.poll(0)
            total += sent
            log.info("Регион %-18s получено=%d отправлено=%d", name, len(aircraft), sent)
            time.sleep(REQUEST_PAUSE_SEC)

        producer.flush(10)
        log.info("Цикл завершён: отправлено %d событий", total)
        end = cycle_start + POLL_INTERVAL_SEC
        while running and time.time() < end:
            time.sleep(0.5)

    producer.flush(10)
    log.info("Продюсер остановлен")


if __name__ == "__main__":
    main()
