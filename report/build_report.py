import copy
from pathlib import Path

import docx
from docx.shared import Cm

TEMPLATE = Path(r"C:\Users\palppv\Downloads\Telegram Desktop\Levina_BBI-23-УП-2_BD_1.docx")
SHOTS = Path(__file__).parent / "screenshots"
OUT = Path(__file__).parent / "Отчет_Flight_Data_Platform.docx"

TITLE = "Проект"
SUBJECT = " «Проектирование систем обработки больших данных»"
TOPIC = "на тему «Data-платформа для анализа воздушного движения»"

INTRO = (
    "В рамках проекта была разработана data-платформа Flight Data Platform для сбора, хранения и анализа "
    "данных о воздушном движении. Данные поступают из внешнего источника, открытого ADS-B API adsb.lol, "
    "передаются через брокер сообщений Apache Kafka, обрабатываются движком Apache Spark и сохраняются в "
    "lakehouse-хранилище на основе Delta Lake с разделением на слои bronze, silver и gold. Оркестрацию "
    "процессов выполняет Apache Airflow. На основе слоя gold построены аналитические витрины, дашборды "
    "Streamlit и ИИ-агент на локальной языковой модели, который отвечает на вопросы пользователя, обращаясь "
    "к витринам. Все компоненты запускаются в контейнерах Docker Compose."
)

STEPS = [
    ("Общая архитектура решения включает источник данных, брокер сообщений, движок обработки, трёхслойное "
     "хранилище, оркестратор и потребителей витрин. Схема взаимодействия компонентов представлена на рисунке.",
     "arch", "Архитектура платформы"),
    ("Инфраструктура описана в файле docker-compose.yml. В него вошли Apache Kafka в режиме KRaft без "
     "Zookeeper, Kafka UI для мониторинга, S3-совместимое хранилище SeaweedFS, база PostgreSQL для метаданных "
     "Airflow, а также сервисы продюсера, Airflow и приложения. На рисунке показан фрагмент конфигурации "
     "брокера Kafka.",
     "c01_compose", "Файл конфигурации Docker Compose"),
    ("После сборки образов был выполнен запуск контейнеров. Все сервисы успешно развёрнуты, контейнеры "
     "Kafka, SeaweedFS и PostgreSQL прошли проверки работоспособности.",
     "t01_compose_ps", "Запущенные контейнеры Docker"),
    ("Для передачи событий в Kafka создан топик flights.raw с тремя партициями. Ключом сообщения служит "
     "идентификатор воздушного судна ICAO24, поэтому события одного самолёта попадают в одну партицию и "
     "сохраняют порядок.",
     "t02_topic", "Параметры топика Kafka"),
    ("Сбор данных реализован программой-продюсером. Она каждые 60 секунд опрашивает API adsb.lol по шести "
     "регионам с плотным воздушным движением (Франкфурт, Лондон, Стамбул, Нью-Йорк, Дубай, Сингапур) и "
     "публикует состояние каждого самолёта отдельным JSON-событием. Ошибки сети обрабатываются без "
     "остановки сервиса.",
     "c02_producer", "Исходный код модуля Producer"),
    ("После запуска продюсера в лог выводится количество полученных и отправленных событий по каждому "
     "региону. За один цикл в Kafka поступает порядка полутора тысяч сообщений.",
     "t03_producer_log", "Результат работы Producer"),
    ("Поступление данных можно наблюдать в интерфейсе Kafka UI. В топике накапливаются события с "
     "позывным, регистрацией, координатами, высотой и скоростью самолётов.",
     "02_kafka_messages", "Сообщения топика flights.raw в Kafka UI"),
    ("Хранилище организовано по принципу lakehouse: данные в формате Delta Lake лежат в бакете lakehouse "
     "S3-совместимого хранилища SeaweedFS. Слои bronze, silver и gold расположены в отдельных каталогах, "
     "рядом находятся служебные каталоги контрольных точек потоковой обработки.",
     "03_lake_lakehouse", "Структура lakehouse-хранилища"),
    ("Первый слой, bronze, формируется заданием Spark Structured Streaming. Оно читает топик Kafka и "
     "добавляет сообщения в таблицу Delta без изменений, вместе с метаданными (партиция, смещение, время). "
     "Режим availableNow позволяет Airflow запускать обработку по расписанию с сохранением смещений в "
     "контрольной точке.",
     "c03_bronze", "Исходный код задания bronze_ingest"),
    ("Проверка слоя bronze показывает исходные JSON-сообщения и служебные поля Kafka.",
     "t04_bronze_sample", "Пример данных слоя bronze"),
    ("Слой silver строится потоковым чтением таблицы bronze. Для каждой порции данных выполняются разбор "
     "JSON по явной схеме, приведение типов, расчёт времени фактической позиции, фильтрация недопустимых "
     "значений координат, высоты и скорости. Запись выполняется командой MERGE, поэтому повторный запуск "
     "не создаёт дубликатов.",
     "c04_silver", "Исходный код задания silver_transform"),
    ("В слое silver данные представлены типизированной таблицей позиций самолётов с признаком нахождения "
     "на земле, высотой в футах и скоростью в узлах.",
     "t05_silver_sample", "Пример данных слоя silver"),
    ("Слой gold содержит семь витрин: текущие позиции самолётов, почасовой трафик по регионам, активность "
     "авиакомпаний, статистику по типам судов, суточную сводку по бортам, аварийные сигналы и активность "
     "аэропортов. Для последней витрины используется справочник аэропортов OurAirports, который "
     "ежедневно загружается отдельным DAG. Ниже показан код расчёта витрины аэропортов: по расстоянию "
     "до аэропорта и вертикальной скорости определяются прилетающие и вылетающие самолёты.",
     "c05_gold", "Исходный код формирования витрины аэропортов"),
    ("Готовые витрины сохранены в каталоге gold в формате Delta.",
     "06_lake_gold", "Витрины слоя gold в хранилище"),
    ("Оркестрацию выполняет Apache Airflow. DAG flights_lakehouse_pipeline запускается каждые 10 минут "
     "и последовательно выполняет задания bronze_ingest, silver_transform и gold_marts. Параллельные "
     "запуски запрещены, неудачные задания перезапускаются автоматически.",
     "c06_dag", "Исходный код DAG flights_lakehouse_pipeline"),
    ("В веб-интерфейсе Airflow видны оба DAG: основной конвейер и ежедневная загрузка справочника "
     "аэропортов.",
     "07_airflow_dags", "Список DAG в Airflow"),
    ("Граф задач отражает последовательность обработки данных по слоям.",
     "09_airflow_graph", "Граф DAG flights_lakehouse_pipeline"),
    ("Сетка запусков подтверждает, что все задания конвейера успешно выполняются по расписанию.",
     "08_airflow_grid", "История запусков DAG"),
    ("Для аналитики построен дашборд Streamlit, читающий витрины gold напрямую из Delta-таблиц. На нём "
     "отображаются ключевые показатели и карта самолётов, окрашенных по высоте полёта.",
     "10_dashboard_top", "Дашборд: показатели и карта самолётов"),
    ("Ниже расположены графики трафика по регионам, популярных типов самолётов, авиакомпаний и "
     "загруженности аэропортов.",
     "11_dashboard_charts", "Дашборд: аналитические графики"),
    ("ИИ-агент реализован по схеме text-to-SQL. Он получает описание витрин и вопрос пользователя, "
     "запрашивает у локальной модели qwen3:8b (Ollama) SQL-запрос, проверяет его на безопасность "
     "(разрешён только SELECT), выполняет в DuckDB по витринам gold и формирует ответ на основе "
     "полученной таблицы. При ошибке запроса агент один раз пытается исправить его автоматически.",
     "c07_agent", "Исходный код ИИ-агента"),
    ("Пример работы агента: на вопрос о самых частых типах самолётов он построил запрос к витрине "
     "mart_aircraft_types и сформулировал ответ по результату.",
     "13_agent_1", "Ответ ИИ-агента о типах самолётов"),
    ("Ещё один пример: вопрос о самом загруженном аэропорте решается обращением к витрине "
     "mart_airport_activity, содержащей данные справочника OurAirports.",
     "13_agent_2", "Ответ ИИ-агента об аэропортах"),
]

CONCLUSION = (
    "В ходе выполнения проекта разработана целостная data-платформа: данные о воздушном движении "
    "собираются из внешнего открытого API, передаются через Apache Kafka, обрабатываются Apache Spark, "
    "сохраняются в lakehouse-хранилище Delta Lake по слоям bronze, silver и gold и преобразуются в "
    "аналитические витрины. Работу конвейера по расписанию обеспечивает Apache Airflow. Витрины доступны "
    "как для визуальной аналитики в дашборде, так и для обращения через ИИ-агента на локальной языковой "
    "модели, отвечающего на основе данных проекта. Все требования технического задания выполнены, а "
    "решение целиком воспроизводится запуском Docker Compose."
)


def set_text(paragraph, text):
    runs = paragraph.runs
    if not runs:
        paragraph.add_run(text)
        return
    runs[0].text = text
    for r in runs[1:]:
        r.text = ""


def main():
    doc = docx.Document(str(TEMPLATE))
    paragraphs = doc.paragraphs
    set_text(paragraphs[8], TITLE)
    set_text(paragraphs[10], SUBJECT)
    set_text(paragraphs[11], TOPIC)

    table = doc.tables[0]
    for row_idx in (1, 5):
        for cell in table.rows[row_idx].cells:
            for p in cell.paragraphs:
                set_text(p, "")

    text_tpl = copy.deepcopy(paragraphs[25]._p)
    img_tpl = copy.deepcopy(paragraphs[26]._p)
    cap_tpl = copy.deepcopy(paragraphs[27]._p)

    body = doc.element.body
    for p in paragraphs[25:]:
        body.remove(p._p)
    for rid, rel in list(doc.part.rels.items()):
        if rel.reltype.endswith("/image"):
            del doc.part.rels[rid]

    sect = body.find(docx.oxml.ns.qn("w:sectPr"))

    def add_text(text):
        el = copy.deepcopy(text_tpl)
        sect.addprevious(el)
        para = docx.text.paragraph.Paragraph(el, doc._body)
        set_text(para, text)

    def add_figure(image, caption, number):
        el = copy.deepcopy(img_tpl)
        for r in el.findall(docx.oxml.ns.qn("w:r")):
            el.remove(r)
        sect.addprevious(el)
        para = docx.text.paragraph.Paragraph(el, doc._body)
        picture = para.add_run().add_picture(str(SHOTS / f"{image}.png"))
        max_w, max_h = Cm(15.5), Cm(19)
        ratio = min(max_w / picture.width, max_h / picture.height, 1.0)
        picture.width = int(picture.width * ratio)
        picture.height = int(picture.height * ratio)
        cap = copy.deepcopy(cap_tpl)
        sect.addprevious(cap)
        cap_para = docx.text.paragraph.Paragraph(cap, doc._body)
        set_text(cap_para, f"Рисунок {number} – {caption}")

    add_text(INTRO)
    for n, (text, image, caption) in enumerate(STEPS, 1):
        add_text(text)
        add_figure(image, caption, n)
    add_text(CONCLUSION)

    props = doc.core_properties
    props.author = ""
    props.last_modified_by = ""
    props.title = "Flight Data Platform"
    props.comments = ""
    props.subject = ""
    props.keywords = ""
    doc.save(str(OUT))
    print("saved", OUT, "figures:", len(STEPS))


if __name__ == "__main__":
    main()
