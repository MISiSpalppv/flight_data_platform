from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

SHOTS = Path(__file__).parent / "screenshots"
BUILD = Path(__file__).parent / "_build"
BUILD.mkdir(exist_ok=True)
OUT = Path(__file__).parent / "Презентация_Flight_Data_Platform_v2.pptx"

PAPER = RGBColor(0xF5, 0xF2, 0xEB)
INK = RGBColor(0x16, 0x1F, 0x33)
ORANGE = RGBColor(0xE8, 0x5D, 0x04)
BLUE = RGBColor(0x1D, 0x4E, 0x89)
MUTED = RGBColor(0x6B, 0x72, 0x80)
LINE = RGBColor(0xD6, 0xD1, 0xC4)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
HEAD_FONT = "Georgia"
BODY_FONT = "Segoe UI"
MONO_FONT = "Consolas"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def crop(name, box, out_name):
    img = Image.open(SHOTS / f"{name}.png")
    box = (box[0], box[1], min(box[2], img.width), min(box[3], img.height))
    img.crop(box).save(BUILD / f"{out_name}.png")
    return BUILD / f"{out_name}.png"


def rect(slide, x, y, w, h, color):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def text(slide, content, x, y, w, h, size=18, bold=False, color=INK, font=BODY_FONT,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=None):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    lines = content if isinstance(content, list) else [content]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if spacing:
            p.space_after = Pt(spacing)
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.name = font
        r.font.color.rgb = color
    return box


def new_slide(number, label, title):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = PAPER
    text(s, f"{number:02d}", 0.7, 0.5, 0.9, 0.5, size=16, bold=True, color=ORANGE, font=MONO_FONT)
    text(s, label.upper(), 1.45, 0.52, 6, 0.4, size=12, color=MUTED, font=MONO_FONT)
    text(s, title, 0.7, 0.95, 11.9, 0.9, size=34, bold=True, font=HEAD_FONT)
    return s


def picture(slide, path, x, y, w, h, frame=True, align="center", valign="center"):
    img = Image.open(path)
    ratio = min(w / img.width, h / img.height)
    pw, ph = img.width * ratio, img.height * ratio
    px = x + (w - pw) / 2 if align == "center" else x
    py = y + (h - ph) / 2 if valign == "center" else y
    pic = slide.shapes.add_picture(str(path), Inches(px), Inches(py), Inches(pw), Inches(ph))
    if frame:
        pic.line.color.rgb = LINE
        pic.line.width = Pt(1)
    return px, py, pw, ph


def caption(slide, content, x, y, w):
    text(slide, content, x, y, w, 0.3, size=11, color=MUTED, font=MONO_FONT)


# 01. Титул
s = prs.slides.add_slide(BLANK)
s.background.fill.solid()
s.background.fill.fore_color.rgb = PAPER
rect(s, 0.7, 1.3, 0.9, 0.08, ORANGE)
text(s, "Flight Data\nPlatform".split("\n"), 0.7, 1.6, 6.0, 2.4, size=56, bold=True, font=HEAD_FONT)
text(s, "Платформа данных о воздушном движении: от ADS-B сигнала до вопроса к ИИ-агенту", 0.7, 4.15, 5.4, 1.3, size=20, color=BLUE)
text(s, ["Проектирование систем обработки больших данных", "НИТУ «МИСИС», 38.03.05 Бизнес-информатика"], 0.7, 6.1, 5.8, 0.8, size=12, color=MUTED, font=MONO_FONT, spacing=3)
map_img = crop("10_dashboard_top", (416, 428, 1293, 980), "title_map")
pic = s.shapes.add_picture(str(map_img), Inches(6.5), Inches(1.3), Inches(6.833), Inches(4.3))
rect(s, 6.5, 5.6, 6.833, 0.55, INK)
text(s, "самолёты над Европой и Атлантикой, данные на момент съёмки", 6.7, 5.6, 6.4, 0.55, size=12, color=WHITE, font=MONO_FONT, anchor=MSO_ANCHOR.MIDDLE)

# 02. Задача
s = new_slide(2, "Задача", "Семь требований ТЗ, один сквозной конвейер")
items = [
    ("Lakehouse", "Delta Lake, слои bronze / silver / gold"),
    ("Движок обработки", "Apache Spark"),
    ("Брокер сообщений", "Apache Kafka"),
    ("Оркестрация", "Apache Airflow"),
    ("Внешний источник", "adsb.lol API и справочник OurAirports"),
    ("Витрины", "7 таблиц слоя gold"),
    ("ИИ-агент", "локальная qwen3:8b, text-to-SQL"),
]
for i, (name, impl) in enumerate(items):
    col, row = divmod(i, 4)
    x = 0.7 + col * 6.2
    y = 2.2 + row * 1.15
    text(s, str(i + 1), x, y, 0.6, 0.8, size=36, bold=True, color=ORANGE, font=HEAD_FONT)
    text(s, name, x + 0.75, y + 0.02, 5.0, 0.4, size=19, bold=True)
    text(s, impl, x + 0.75, y + 0.45, 5.0, 0.4, size=15, color=MUTED)
    rect(s, x, y + 0.95, 5.6, 0.01, LINE)
text(s, "Данные не берутся из готового файла: самолёты приходят из живого API каждую минуту.", 6.9, 6.35, 5.8, 0.8, size=14, color=BLUE)

# 03. Архитектура
s = new_slide(3, "Архитектура", "Как данные проходят через систему")
picture(s, SHOTS / "arch.png", 0.7, 1.9, 11.9, 5.2, frame=False)

# 04. Сбор данных
s = new_slide(4, "Сбор данных", "Самолёты приходят из внешнего API")
for i, (num, label) in enumerate([("6", "регионов: Европа, США, Ближний Восток, Азия"), ("60 с", "интервал опроса adsb.lol"), ("≈1500", "событий за один цикл в Kafka")]):
    y = 2.1 + i * 1.5
    text(s, num, 0.7, y, 3.2, 0.9, size=48, bold=True, color=ORANGE, font=HEAD_FONT)
    text(s, label, 0.7, y + 0.95, 3.8, 0.5, size=14, color=MUTED)
px, py, pw, ph = picture(s, crop("02_kafka_messages", (200, 60, 1500, 760), "kafka"), 4.9, 2.0, 7.8, 4.2)
caption(s, "Kafka UI: топик flights.raw, ключ сообщения: ICAO24 самолёта", 4.9, py + ph + 0.12, 7.8)

# 05. Lakehouse
s = new_slide(5, "Lakehouse", "Три слоя: от сырых событий к витринам")
rows = [
    ("BRONZE", "События Kafka как есть,\nтолько добавление", crop("t04_bronze_sample", (0, 0, 1398, 212), "l_bronze")),
    ("SILVER", "Разбор JSON, типы, фильтры,\nдедупликация через MERGE", crop("t05_silver_sample", (0, 40, 1227, 286), "l_silver")),
    ("GOLD", "Семь витрин в формате Delta\nв хранилище S3", crop("06_lake_gold", (150, 120, 1350, 470), "l_gold")),
]
colors = [RGBColor(0xB4, 0x6B, 0x2C), RGBColor(0x6B, 0x72, 0x80), RGBColor(0xC9, 0x9A, 0x06)]
for i, (name, desc, img) in enumerate(rows):
    y = 2.0 + i * 1.7
    rect(s, 0.7, y, 0.09, 1.45, colors[i])
    text(s, name, 1.0, y, 3.0, 0.45, size=22, bold=True, font=HEAD_FONT, color=colors[i])
    text(s, desc.split("\n"), 1.0, y + 0.55, 3.4, 0.9, size=13, color=MUTED)
    picture(s, img, 4.6, y, 8.1, 1.5, align="left")

# 06. Spark и Airflow
s = new_slide(6, "Обработка и оркестрация", "Spark считает, Airflow следит за расписанием")
px, py, pw, ph = picture(s, SHOTS / "c04_silver.png", 0.7, 2.0, 6.4, 4.6, valign="top")
caption(s, "silver: потоковое чтение bronze и идемпотентный MERGE", 0.7, py + ph + 0.12, 6.4)
px, py, pw, ph = picture(s, crop("09_airflow_graph", (320, 230, 1260, 640), "air_graph"), 7.5, 2.0, 5.2, 2.6, valign="top")
caption(s, "DAG каждые 10 минут: bronze, silver, gold", 7.5, py + ph + 0.12, 5.2)
text(s, ["Spark Structured Streaming в режиме availableNow: смещения Kafka хранятся в контрольной точке.", "Справочник аэропортов обновляет отдельный DAG раз в сутки."], 7.5, 5.0, 5.2, 1.8, size=14, color=INK, spacing=8)

# 07. Витрины
s = new_slide(7, "Витрины", "Семь таблиц слоя gold")
marts = [
    ("mart_live_aircraft", "где сейчас самолёты: позиции за 10 минут"),
    ("mart_traffic_region_hour", "трафик по регионам по часам"),
    ("mart_airline_activity", "борты и рейсы авиакомпаний"),
    ("mart_aircraft_types", "статистика по типам судов"),
    ("mart_aircraft_daily", "сводка по каждому борту за день"),
    ("mart_emergency_events", "аварийные сигналы 7500 / 7600 / 7700"),
    ("mart_airport_activity", "прилёты и вылеты у аэропортов"),
]
for i, (name, desc) in enumerate(marts):
    y = 2.1 + i * 0.7
    text(s, name, 0.7, y, 5.2, 0.5, size=18, bold=True, color=ORANGE, font=MONO_FONT)
    text(s, desc, 6.1, y + 0.02, 6.6, 0.5, size=17)
    rect(s, 0.7, y + 0.55, 12.0, 0.01, LINE)

# 08. Дашборд
s = new_slide(8, "Дашборд", "Живая карта и аналитика поверх витрин")
dash = crop("10_dashboard_top", (336, 230, 1440, 980), "dash")
px, py, pw, ph = picture(s, dash, 0.7, 1.95, 7.4, 5.0)
charts = crop("11_dashboard_charts", (400, 20, 1440, 560), "charts")
picture(s, charts, 8.4, 1.95, 4.3, 2.3)
text(s, ["Графики строятся из тех же Delta-таблиц: трафик по регионам, типы самолётов, авиакомпании, загруженность аэропортов.", "Читает приложение напрямую из S3, без Spark."], 8.4, 4.6, 4.3, 2.2, size=14, spacing=10)

# 09. ИИ-агент
s = new_slide(9, "ИИ-агент", "Вопрос на русском, ответ из данных")
steps = ["Вопрос", "SQL по витринам", "DuckDB", "Ответ"]
x = 0.7
for i, step in enumerate(steps):
    w = 2.35
    chip = s.shapes.add_shape(MSO_SHAPE.PENTAGON if i < len(steps) - 1 else MSO_SHAPE.RECTANGLE, Inches(x), Inches(1.95), Inches(w), Inches(0.6))
    chip.fill.solid()
    chip.fill.fore_color.rgb = INK if i % 2 == 0 else BLUE
    chip.line.fill.background()
    chip.shadow.inherit = False
    tf = chip.text_frame
    tf.text = step
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.paragraphs[0].runs[0].font.size = Pt(15)
    tf.paragraphs[0].runs[0].font.name = BODY_FONT
    tf.paragraphs[0].runs[0].font.color.rgb = WHITE
    x += w + 0.1
text(s, "qwen3:8b, Ollama, только SELECT", 10.75, 1.95, 2.0, 0.6, size=10, color=MUTED, font=MONO_FONT, anchor=MSO_ANCHOR.MIDDLE)
a1 = crop("13_agent_1", (416, 440, 1420, 1250), "agent1")
a2 = crop("13_agent_2", (416, 440, 1420, 830), "agent2")
picture(s, a1, 0.7, 2.85, 6.0, 4.1, valign="top")
picture(s, a2, 6.95, 2.85, 5.75, 4.1, valign="top")

# 10. Итоги
s = new_slide(10, "Итоги", "Что получилось")
facts = [
    ("1", "команда запуска: docker compose up"),
    ("3", "слоя данных, 7 витрин, 2 DAG"),
    ("10 мин", "цикл обновления витрин по расписанию Airflow"),
]
for i, (num, label) in enumerate(facts):
    x = 0.7 + i * 4.1
    text(s, num, x, 2.2, 3.6, 1.1, size=60, bold=True, color=ORANGE, font=HEAD_FONT)
    text(s, label, x, 3.4, 3.5, 0.9, size=16, color=INK)
rect(s, 0.7, 4.7, 12.0, 0.01, LINE)
text(s, "Дальше", 0.7, 5.0, 2.0, 0.4, size=14, bold=True, color=BLUE, font=MONO_FONT)
text(s, "больше регионов и история за недели, оповещения об аварийных сигналах, векторный поиск по описаниям витрин для агента", 2.7, 5.0, 10.0, 1.2, size=17)

prs.core_properties.author = ""
prs.core_properties.last_modified_by = ""
prs.core_properties.title = "Flight Data Platform"
prs.save(str(OUT))
print("saved", OUT)
