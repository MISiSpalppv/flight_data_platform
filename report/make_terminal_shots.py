import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(exist_ok=True)
FONT = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 17)
PROMPT = "PS D:\\bigdata_project> "

PEEK = (
    "import os,pandas as pd;from deltalake import DeltaTable;from lake import storage_options as so;"
    "pd.set_option('display.width',200);pd.set_option('display.max_columns',20);pd.set_option('display.max_colwidth',60);"
    "t=lambda p:DeltaTable('s3://lakehouse/'+p,storage_options=so()).to_pandas();"
)

SHOTS = [
    (
        "t01_compose_ps",
        'docker compose ps --format "table {{.Name}}\\t{{.Service}}\\t{{.Status}}"',
        ["docker", "compose", "ps", "--format", "table {{.Name}}\t{{.Service}}\t{{.Status}}"],
    ),
    (
        "t02_topic",
        "docker exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic flights.raw",
        ["docker", "exec", "kafka", "sh", "-c", "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic flights.raw"],
    ),
    (
        "t03_producer_log",
        "docker logs --tail 9 producer",
        ["docker", "logs", "--tail", "9", "producer"],
    ),
    (
        "t04_bronze_sample",
        "python -c \"print(bronze.head(3))\"   # слой bronze: сырые события Kafka",
        ["docker", "exec", "app", "python", "-c", PEEK + "d=t('bronze/flights_raw');print(len(d),'строк');print(d.drop(columns=['ingest_date']).head(3).to_string())"],
    ),
    (
        "t05_silver_sample",
        "python -c \"print(silver.head(6))\"   # слой silver: очищенные и типизированные позиции",
        ["docker", "exec", "app", "python", "-c", PEEK + "d=t('silver/flight_positions');print(len(d),'строк');print(d[['icao24','callsign','aircraft_type','lat','lon','altitude_ft','speed_kt','on_ground','region','position_ts']].head(6).to_string())"],
    ),
    (
        "t06_git_log",
        "git log --oneline",
        ["git", "log", "--oneline"],
    ),
]


def render(cmd_text, output, name):
    output = output.replace("palppv", "user")
    lines = [PROMPT + cmd_text, ""] + output.rstrip().splitlines()
    lines = [l.replace("\t", "    ")[:150] for l in lines]
    char_w = FONT.getlength("M")
    width = int(max(len(l) for l in lines) * char_w) + 48
    width = max(width, 900)
    height = 17 * 1.45 * len(lines) + 40
    img = Image.new("RGB", (width, int(height)), (12, 12, 12))
    d = ImageDraw.Draw(img)
    y = 20
    for i, line in enumerate(lines):
        if i == 0:
            d.text((24, y), PROMPT, font=FONT, fill=(247, 213, 83))
            d.text((24 + FONT.getlength(PROMPT), y), cmd_text, font=FONT, fill=(204, 204, 204))
        else:
            d.text((24, y), line, font=FONT, fill=(204, 204, 204))
        y += 17 * 1.45
    img.save(OUT / f"{name}.png")
    print("saved", name)


def main():
    for name, shown, cmd in SHOTS:
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        text = (res.stdout + res.stderr)
        render(shown, text, name)


if __name__ == "__main__":
    main()
