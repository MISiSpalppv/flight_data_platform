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
OUT = Path(__file__).parent / "Презентация_Flight_Data_Platform.pptx"

BG = RGBColor(0x0F, 0x1B, 0x2D)
CARD = RGBColor(0x17, 0x28, 0x40)
ACCENT = RGBColor(0x38, 0xBD, 0xF8)
ORANGE = RGBColor(0xF5, 0x9E, 0x0B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
MUTED = RGBColor(0xA9, 0xB8, 0xCC)
FONT = "Segoe UI"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def crop(name, box, out_name):
    img = Image.open(SHOTS / f"{name}.png")
    box = (box[0], box[1], min(box[2], img.width), min(box[3], img.height))
    img.crop(box).save(BUILD / f"{out_name}.png")
    return BUILD / f"{out_name}.png"


def new_slide(title, number=None):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(0.5), Inches(0.12), Inches(0.62))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()
    text(s, title, 0.9, 0.4, 11.5, 0.85, size=32, bold=True)
    if number:
        text(s, str(number), 12.2, 6.95, 0.7, 0.4, size=12, color=MUTED, align=PP_ALIGN.RIGHT)
    return s


def text(slide, content, x, y, w, h, size=18, bold=False, color=WHITE, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    lines = content if isinstance(content, list) else [content]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.name = FONT
        r.font.color.rgb = color
    return box


def bullets(slide, items, x, y, w, h, size=18):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(10)
        dot = p.add_run()
        dot.text = "●  "
        dot.font.size = Pt(size - 6)
        dot.font.color.rgb = ACCENT
        dot.font.name = FONT
        r = p.add_run()
        r.text = item
        r.font.size = Pt(size)
        r.font.name = FONT
        r.font.color.rgb = WHITE
    return box


def card(slide, x, y, w, h):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.adjustments[0] = 0.04
    shape.fill.solid()
    shape.fill.fore_color.rgb = CARD
    shape.line.fill.background()
    return shape


def picture(slide, path, x, y, w, h, caption=None):
    img = Image.open(path)
    ratio = min(w / img.width, h / img.height)
    pw, ph = img.width * ratio, img.height * ratio
    px, py = x + (w - pw) / 2, y + (h - ph) / 2
    slide.shapes.add_picture(str(path), Inches(px), Inches(py), Inches(pw), Inches(ph))
    if caption:
        text(slide, caption, x, y + h + 0.02, w, 0.35, size=12, color=MUTED, align=PP_ALIGN.CENTER)


def table(slide, rows, x, y, w, col_widths, size=13, row_h=0.46):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows)))
    tbl = shape.table
    for c, cw in enumerate(col_widths):
        tbl.columns[c].width = Inches(cw)
    for r, row in enumerate(rows):
        tbl.rows[r].height = Inches(row_h)
        for c, value in enumerate(row):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = ACCENT if r == 0 else (CARD if r % 2 else RGBColor(0x1E, 0x33, 0x50))
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            run = p.add_run()
            run.text = value
            run.font.size = Pt(size)
            run.font.name = FONT
            run.font.bold = r == 0
            run.font.color.rgb = BG if r == 0 else WHITE
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    return tbl


# 1. Титульный слайд
s = prs.slides.add_slide(BLANK)
s.background.fill.solid()
s.background.fill.fore_color.rgb = BG
band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(3.0), prs.slide_width, Inches(0.08))
band.fill.solid()
band.fill.fore_color.rgb = ACCENT
band.line.fill.background()
text(s, "Flight Data Platform", 0.9, 1.4, 11.5, 1.2, size=54, bold=True)
text(s, "Data-платформа для анализа воздушного движения в реальном времени", 0.9, 3.3, 11.5, 0.9, size=26, color=ACCENT)
text(s, "Lakehouse · Kafka · Spark · Airflow · ИИ-агент", 0.9, 4.2, 11.5, 0.6, size=20, color=MUTED)
text(s, ["Проектирование систем обработки больших данных", "38.03.05 Бизнес-информатика, НИТУ «МИСИС»"], 0.9, 5.7, 11.5, 1.0, size=16, color=MUTED)

# 2. Цель и требования
s = new_slide("Цель проекта и требования ТЗ", 2)
bullets(
    s,
    [
        "Собрать данные воздушного движения из внешнего API",
        "Провести их через потоковый и пакетный конвейер",
        "Хранить в lakehouse по слоям и строить витрины",
        "Дать доступ к данным через дашборды и ИИ-агента",
    ],
    0.7, 1.6, 5.0, 4.5, size=20,
)
table(
    s,
    [
        ["Требование ТЗ", "Реализация"],
        ["Lakehouse по слоям", "Delta Lake, bronze/silver/gold"],
        ["Движок обработки", "Apache Spark (PySpark)"],
        ["Брокер сообщений", "Apache Kafka (KRaft)"],
        ["Оркестрация", "Apache Airflow"],
        ["Внешний источник", "adsb.lol API + OurAirports"],
        ["Витрины", "7 таблиц слоя gold"],
        ["ИИ-агент", "Ollama qwen3:8b, text-to-SQL"],
    ],
    6.0, 1.6, 6.7, [2.7, 4.0], size=15, row_h=0.6,
)

# 3. Архитектура
s = new_slide("Архитектура платформы", 3)
picture(s, SHOTS / "arch.png", 0.8, 1.35, 11.7, 5.6)

# 4. Сбор данных и Kafka
s = new_slide("Сбор данных: ADS-B API → Kafka", 4)
bullets(
    s,
    [
        "adsb.lol: открытый ADS-B API без ключа, живые данные",
        "6 регионов, опрос каждые 60 секунд",
        "≈1500 событий за цикл, ключ сообщения: ICAO24",
        "Топик flights.raw: 3 партиции, режим KRaft",
    ],
    0.7, 1.5, 12, 2.2, size=18,
)
card(s, 0.6, 3.7, 5.6, 3.0)
card(s, 6.5, 3.7, 6.2, 3.0)
picture(s, crop("t03_producer_log", (0, 0, 1000, 300), "p_log"), 0.7, 3.8, 5.4, 2.8, "Лог продюсера")
picture(s, crop("02_kafka_messages", (200, 60, 1500, 700), "k_msgs"), 6.6, 3.8, 6.0, 2.8, "Kafka UI: сообщения топика")

# 5. Lakehouse
s = new_slide("Lakehouse: Delta Lake на S3-хранилище", 5)
layers = [
    ("Bronze", "сырые события Kafka без изменений", ORANGE),
    ("Silver", "типы, фильтры, дедупликация MERGE", MUTED),
    ("Gold", "7 витрин для аналитики и агента", RGBColor(0xFA, 0xCC, 0x15)),
]
for i, (name, desc, color) in enumerate(layers):
    y = 1.5 + i * 1.45
    card(s, 0.6, y, 5.3, 1.25)
    chip = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(y + 0.3), Inches(1.5), Inches(0.65))
    chip.fill.solid()
    chip.fill.fore_color.rgb = color
    chip.line.fill.background()
    chip.text_frame.text = name
    chip.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    chip.text_frame.paragraphs[0].runs[0].font.size = Pt(18)
    chip.text_frame.paragraphs[0].runs[0].font.bold = True
    chip.text_frame.paragraphs[0].runs[0].font.name = FONT
    chip.text_frame.paragraphs[0].runs[0].font.color.rgb = BG
    text(s, desc, 2.45, y + 0.2, 3.35, 0.9, size=15, anchor=MSO_ANCHOR.MIDDLE)
card(s, 6.2, 1.5, 6.5, 4.25)
picture(s, crop("t05_silver_sample", (0, 40, 1236, 285), "silver"), 6.3, 1.6, 6.3, 2.2, "Слой silver: типизированные позиции")
picture(s, crop("06_lake_gold", (150, 120, 1350, 470), "gold_dir"), 6.3, 3.85, 6.3, 1.85, "Витрины слоя gold в хранилище")
text(s, "Формат Delta: ACID-транзакции, MERGE, схема и история версий", 0.6, 6.05, 12, 0.6, size=16, color=ACCENT)

# 6. Spark и Airflow
s = new_slide("Обработка в Spark и оркестрация в Airflow", 6)
card(s, 0.6, 1.5, 6.1, 4.9)
picture(s, SHOTS / "c04_silver.png", 0.7, 1.6, 5.9, 4.3, "silver: потоковое чтение bronze + MERGE")
card(s, 7.0, 1.5, 5.7, 3.1)
picture(s, SHOTS / "09_airflow_graph.png", 7.1, 1.6, 5.5, 2.9, "DAG: bronze → silver → gold")
bullets(
    s,
    ["Запуск каждые 10 минут, без параллельных прогонов", "Spark: Structured Streaming, режим availableNow", "Справочник аэропортов: отдельный DAG раз в сутки"],
    7.0, 4.75, 5.8, 2.0, size=15,
)

# 7. Витрины
s = new_slide("Витрины данных (слой gold)", 7)
table(
    s,
    [
        ["Витрина", "Содержание"],
        ["mart_live_aircraft", "текущие позиции самолётов за 10 минут"],
        ["mart_traffic_region_hour", "почасовой трафик по регионам"],
        ["mart_airline_activity", "борты и рейсы авиакомпаний по дням"],
        ["mart_aircraft_types", "статистика по типам воздушных судов"],
        ["mart_aircraft_daily", "сводка по каждому борту за день"],
        ["mart_emergency_events", "аварийные сигналы 7500 / 7600 / 7700"],
        ["mart_airport_activity", "прилёты и вылеты у аэропортов (OurAirports)"],
    ],
    0.8, 1.6, 11.7, [4.4, 7.3], size=17, row_h=0.62,
)

# 8. Дашборд
s = new_slide("Дашборд: воздушное движение в реальном времени", 8)
card(s, 0.6, 1.4, 12.1, 5.45)
picture(s, crop("10_dashboard_top", (336, 80, 1440, 980), "dash"), 0.7, 1.5, 11.9, 5.25)

# 9. ИИ-агент
s = new_slide("ИИ-агент: вопросы к витринам на естественном языке", 9)
bullets(
    s,
    [
        "Локальная модель qwen3:8b через Ollama",
        "Вопрос + описание витрин → SQL-запрос",
        "Проверка: разрешён только SELECT",
        "Выполнение в DuckDB по таблицам gold",
        "Самоисправление запроса при ошибке",
        "Ответ строится только по результату запроса",
    ],
    0.7, 1.5, 4.9, 5.2, size=17,
)
card(s, 5.8, 1.4, 6.9, 5.45)
picture(s, crop("13_agent_2", (336, 440, 1440, 840), "agent"), 5.9, 1.55, 6.7, 5.15)

# 10. Итоги
s = new_slide("Итоги", 10)
bullets(
    s,
    [
        "Работает полный конвейер: API → Kafka → Spark → Delta Lake → витрины",
        "Расписание и перезапуски обеспечивает Airflow",
        "Дашборд и ИИ-агент используют только данные платформы",
        "Всё запускается одной командой: docker compose up",
        "Дальше: больше регионов, история за недели, оповещения о событиях",
    ],
    0.8, 1.7, 11.8, 4.2, size=22,
)
text(s, "Исходный код, Docker Compose и инструкции по запуску: репозиторий проекта", 0.8, 6.2, 11.7, 0.6, size=18, color=ACCENT)

prs.core_properties.author = ""
prs.core_properties.last_modified_by = ""
prs.core_properties.title = "Flight Data Platform"
prs.save(str(OUT))
print("saved", OUT)
