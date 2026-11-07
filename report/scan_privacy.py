import glob
import sys
import zipfile
from pathlib import Path

NEEDLES = ["Лев", "palppv", "Медведев", "Telegram", "Users\\"]
root = Path(__file__).parent

for pattern in ("*.docx", "*.pptx"):
    for path in glob.glob(str(root / pattern)):
        z = zipfile.ZipFile(path)
        hits = []
        for name in z.namelist():
            if name.endswith((".xml", ".rels")):
                data = z.read(name).decode("utf-8", "ignore")
                hits += [(k, name) for k in NEEDLES if k in data]
        print(Path(path).name, "->", hits or "чисто")
        sys.stdout.flush()
