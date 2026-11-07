from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(exist_ok=True)

FONTS = Path(r"C:\Windows\Fonts")
MONO = ImageFont.truetype(str(FONTS / "consola.ttf"), 16)


def snippet(rel_path, start, end=None):
    text = (ROOT / rel_path).read_text(encoding="utf-8")
    i = text.index(start)
    j = text.index(end, i + len(start)) if end else len(text)
    return text[i:j].rstrip("\n")


def render_code(name, code, title):
    lines = code.splitlines()
    lh = 23
    num_w = 46
    width = int(max(MONO.getlength(l.replace("\t", "    ")) for l in lines)) + num_w + 50
    width = max(width, 760)
    height = lh * len(lines) + 70
    img = Image.new("RGB", (width, height), (250, 250, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, 34], fill=(225, 229, 235))
    d.text((14, 8), title, font=ImageFont.truetype(str(FONTS / "segoeui.ttf"), 15), fill=(60, 66, 76))
    d.rectangle([0, 34, num_w, height], fill=(238, 240, 243))
    y = 48
    for n, line in enumerate(lines, 1):
        d.text((8, y), f"{n:>3}", font=MONO, fill=(150, 156, 166))
        color = (120, 126, 136) if line.strip().startswith("#") else (30, 34, 40)
        d.text((num_w + 14, y), line.replace("\t", "    "), font=MONO, fill=color)
        y += lh
    img.save(OUT / f"{name}.png")
    print("saved", name)


def architecture(name="arch"):
    W, H = 1800, 900
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f_b = ImageFont.truetype(str(FONTS / "segoeuib.ttf"), 26)
    f = ImageFont.truetype(str(FONTS / "segoeui.ttf"), 21)
    f_s = ImageFont.truetype(str(FONTS / "segoeui.ttf"), 18)

    def box(x, y, w, h, title, sub, fill, edge, tc=(20, 30, 50)):
        d.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=fill, outline=edge, width=3)
        tw = d.textlength(title, font=f_b)
        d.text((x + (w - tw) / 2, y + 16), title, font=f_b, fill=tc)
        for k, line in enumerate(sub):
            lw = d.textlength(line, font=f_s)
            d.text((x + (w - lw) / 2, y + 62 + k * 26), line, font=f_s, fill=(70, 80, 100))

    def arrow(x1, y1, x2, y2, color=(60, 70, 90)):
        d.line([x1, y1, x2, y2], fill=color, width=4)
        if x2 > x1:
            d.polygon([(x2, y2), (x2 - 16, y2 - 9), (x2 - 16, y2 + 9)], fill=color)
        elif y2 > y1:
            d.polygon([(x2, y2), (x2 - 9, y2 - 16), (x2 + 9, y2 - 16)], fill=color)
        else:
            d.polygon([(x2, y2), (x2 - 9, y2 + 16), (x2 + 9, y2 + 16)], fill=color)

    d.rounded_rectangle([20, 20, W - 20, H - 20], radius=24, outline=(150, 170, 200), width=3)
    d.text((44, 32), "Docker Compose", font=f, fill=(90, 110, 150))

    box(60, 110, 280, 130, "adsb.lol API", ["открытые ADS-B данные", "6 регионов, опрос 60 с"], (255, 244, 214), (230, 170, 40))
    box(400, 110, 260, 130, "Producer", ["Python, requests", "JSON-события"], (225, 240, 255), (70, 130, 210))
    box(720, 110, 260, 130, "Apache Kafka", ["топик flights.raw", "3 партиции, KRaft"], (225, 240, 255), (70, 130, 210))
    box(1040, 110, 300, 130, "Apache Spark", ["PySpark, Structured", "Streaming + batch"], (255, 232, 220), (225, 110, 50))
    arrow(340, 175, 400, 175)
    arrow(660, 175, 720, 175)
    arrow(980, 175, 1040, 175)

    d.rounded_rectangle([60, 330, 1340, 600], radius=20, fill=(240, 247, 240), outline=(80, 160, 90), width=3)
    d.text((84, 344), "Lakehouse: Delta Lake на SeaweedFS (S3)", font=f_b, fill=(30, 90, 50))
    box(100, 410, 340, 150, "Bronze", ["сырые события Kafka", "как есть, append"], (255, 236, 215), (205, 127, 50))
    box(520, 410, 340, 150, "Silver", ["очистка, типы,", "дедупликация (MERGE)"], (236, 240, 247), (130, 145, 170))
    box(940, 410, 360, 150, "Gold", ["7 витрин для аналитики", "и ИИ-агента"], (255, 248, 210), (210, 170, 30))
    arrow(440, 485, 520, 485)
    arrow(860, 485, 940, 485)
    arrow(1190, 240, 1190, 330)

    box(1420, 110, 330, 130, "Apache Airflow", ["DAG каждые 10 минут", "bronze → silver → gold"], (240, 230, 250), (140, 90, 190))
    d.line([1420, 175, 1340, 175], fill=(140, 90, 190), width=3)
    d.text((1346, 140), "запуск", font=f_s, fill=(140, 90, 190))
    d.text((1346, 182), "джобов", font=f_s, fill=(140, 90, 190))

    box(1420, 330, 330, 120, "Streamlit", ["дашборды: карта,", "трафик, аэропорты"], (225, 245, 245), (50, 150, 150))
    box(1420, 500, 330, 140, "ИИ-агент", ["Ollama (qwen3:8b)", "text-to-SQL, DuckDB"], (225, 245, 245), (50, 150, 150))
    arrow(1300, 485, 1420, 400)
    arrow(1300, 520, 1420, 560)

    box(60, 680, 500, 130, "OurAirports (CSV)", ["справочник аэропортов,", "ежедневная загрузка DAG"], (255, 244, 214), (230, 170, 40))
    arrow(560, 745, 700, 745)
    d.text((710, 722), "silver.airports → витрина аэропортов", font=f, fill=(70, 80, 100))
    img.save(OUT / f"{name}.png")
    print("saved", name)


if __name__ == "__main__":
    architecture()
    render_code(
        "c01_compose",
        snippet("docker-compose.yml", "  kafka:\n", "  kafka-init:"),
        "docker-compose.yml: сервис Kafka (KRaft)",
    )
    render_code(
        "c02_producer",
        snippet("producer/producer.py", "    while running:", '        producer.flush(10)\n        log.info("Цикл'),
        "producer/producer.py: опрос API и отправка в Kafka",
    )
    render_code(
        "c03_bronze",
        snippet("spark_jobs/bronze_ingest.py", "    raw = (", "    query.awaitTermination()"),
        "spark_jobs/bronze_ingest.py: чтение Kafka и запись в Delta",
    )
    render_code(
        "c04_silver",
        snippet("spark_jobs/silver_transform.py", "def upsert_batch", "if __name__"),
        "spark_jobs/silver_transform.py: идемпотентная загрузка в silver (MERGE)",
    )
    render_code(
        "c05_gold",
        snippet("spark_jobs/gold_marts.py", "def airport_activity", "def main"),
        "spark_jobs/gold_marts.py: витрина активности аэропортов",
    )
    render_code(
        "c06_dag",
        snippet("airflow/dags/flights_lakehouse_pipeline.py", "with DAG("),
        "airflow/dags/flights_lakehouse_pipeline.py",
    )
    render_code(
        "c07_agent",
        snippet("app/agent.py", "def ask", "    if error:"),
        "app/agent.py: цикл text-to-SQL с самоисправлением",
    )
