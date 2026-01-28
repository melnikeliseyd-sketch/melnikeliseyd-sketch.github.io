import os
import json

OUTPUT = "jarvis_index.json"

SEARCH_DIRS = [
    # Диск C:
    "C:\\",

    # Диск K:
    "K:\\",

    # Остальные директории
    os.path.expandvars(r"%ProgramFiles%"),
    os.path.expandvars(r"%ProgramFiles(x86)%"),
    os.path.expandvars(r"%AppData%"),
    os.path.expandvars(r"%LocalAppData%"),
    os.path.expandvars(r"%UserProfile%\\Desktop"),
    os.path.expandvars(r"%UserProfile%\\Downloads"),
    os.path.expandvars(r"%UserProfile%\\Documents"),
    os.path.expandvars(r"%ProgramData%\\Microsoft\\Windows\\Start Menu"),
    os.path.expandvars(r"%AppData%\\Microsoft\\Windows\\Start Menu")
]

EXE_EXTENSIONS = [".exe", ".lnk"]

index = {}


def clean_name(name):
    return name.lower().replace(".exe", "").replace(".lnk", "").replace("-", " ").replace("_", " ").strip()


def scan():
    for base in SEARCH_DIRS:
        if not os.path.exists(base):
            print(f"⚠️  Директория не найдена: {base}")
            continue

        print(f"🔍 Сканирую: {base}")
        for root, dirs, files in os.walk(base):
            for file in files:
                if file.lower().endswith(tuple(EXE_EXTENSIONS)):
                    path = os.path.join(root, file)
                    key = clean_name(file)

                    if key not in index:
                        index[key] = path


def save():
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


print("🔍 Сканирую ПК, это может занять 1–3 минуты...")
scan()
save()
print(f"✅ Найдено программ: {len(index)}")
print("📁 Сохранено в jarvis_index.json")