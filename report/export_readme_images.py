from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(__file__).parent / "screenshots"
DST = ROOT / "docs" / "img"
DST.mkdir(parents=True, exist_ok=True)

JOBS = [
    ("arch", None, "architecture"),
    ("10_dashboard_top", (336, 230, 1440, 980), "dashboard_map"),
    ("11_dashboard_charts", (400, 20, 1440, 560), "dashboard_charts"),
    ("13_agent_1", (416, 440, 1420, 1250), "agent_types"),
    ("13_agent_2", (416, 440, 1420, 830), "agent_airports"),
    ("02_kafka_messages", (200, 60, 1500, 760), "kafka_ui"),
    ("06_lake_gold", (150, 120, 1350, 470), "lake_gold"),
    ("09_airflow_graph", (320, 230, 1260, 640), "airflow_graph"),
    ("08_airflow_grid", None, "airflow_runs"),
    ("t05_silver_sample", None, "silver_sample"),
    ("t04_bronze_sample", None, "bronze_sample"),
    ("07_airflow_dags", None, "airflow_dags"),
]

for name, box, out in JOBS:
    img = Image.open(SRC / f"{name}.png")
    if box:
        img = img.crop((box[0], box[1], min(box[2], img.width), min(box[3], img.height)))
    img = img.convert("RGB")
    if img.width > 1600:
        img = img.resize((1600, int(img.height * 1600 / img.width)))
    img.save(DST / f"{out}.png", optimize=True)
    print(out, img.size, (DST / f"{out}.png").stat().st_size // 1024, "KB")
