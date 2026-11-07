import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(exist_ok=True)

AIRFLOW = "http://localhost:8081"
FILER = "http://localhost:8888"


def shot(page, name, wait=2500, full=False):
    page.wait_for_timeout(wait)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("saved", name)


def main(only=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--enable-webgl"],
        )
        ctx = browser.new_context(viewport={"width": 1500, "height": 900}, locale="ru-RU")
        page = ctx.new_page()

        def want(key):
            return only is None or key in only

        if want("kafka"):
            page.goto("http://localhost:8080/ui/clusters/flight-platform/all-topics")
            shot(page, "01_kafka_topics")
            page.goto("http://localhost:8080/ui/clusters/flight-platform/all-topics/flights.raw/messages")
            shot(page, "02_kafka_messages", wait=4000)

        if want("lake"):
            for i, path in enumerate(["/buckets/lakehouse/", "/buckets/lakehouse/bronze/", "/buckets/lakehouse/silver/", "/buckets/lakehouse/gold/"]):
                page.goto(FILER + path)
                shot(page, f"0{3 + i}_lake_{path.strip('/').split('/')[-1]}")

        if want("airflow"):
            page.goto(AIRFLOW + "/login/")
            page.fill("input[name=username]", "admin")
            page.fill("input[name=password]", "admin")
            page.click("input[type=submit], button[type=submit]")
            page.wait_for_load_state("networkidle")
            page.goto(AIRFLOW + "/home")
            shot(page, "07_airflow_dags")
            page.goto(AIRFLOW + "/dags/flights_lakehouse_pipeline/grid")
            shot(page, "08_airflow_grid", wait=4000)
            page.goto(AIRFLOW + "/dags/flights_lakehouse_pipeline/graph")
            shot(page, "09_airflow_graph", wait=4000)

        if want("app"):
            page.set_viewport_size({"width": 1500, "height": 2600})
            page.goto("http://localhost:8501")
            page.get_by_text("Самолётов в воздухе", exact=True).wait_for(timeout=60000)
            page.wait_for_timeout(12000)
            for name, y0, y1 in [("10_dashboard_top", 0, 980), ("11_dashboard_charts", 980, 1800), ("12_dashboard_bottom", 1800, 2600)]:
                page.screenshot(path=str(OUT / f"{name}.png"), clip={"x": 0, "y": y0, "width": 1500, "height": y1 - y0})
                print("saved", name)
            page.set_viewport_size({"width": 1500, "height": 1250})
            questions = ["Какие 5 типов самолётов встречаются чаще всего?", "Какой самый загруженный аэропорт?"]
            for i, q in enumerate(questions):
                page.goto("http://localhost:8501")
                page.get_by_role("tab", name="ИИ-агент").click()
                box = page.get_by_placeholder("Задайте вопрос о воздушном движении")
                box.fill(q)
                box.press("Enter")
                expect(page.get_by_text("SQL-запрос", exact=True)).to_have_count(1, timeout=300000)
                page.get_by_text("SQL-запрос", exact=True).click()
                expect(page.get_by_text("RUNNING")).to_have_count(0, timeout=60000)
                shot(page, f"13_agent_{i + 1}", wait=2000)

        browser.close()


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
