import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"

# значения по умолчанию на случай, если файла нет
BOT_TOKEN = ""
WORK_CHAT_ID = 0

if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        BOT_TOKEN = data.get("BOT_TOKEN", BOT_TOKEN)
        WORK_CHAT_ID = data.get("WORK_CHAT_ID", WORK_CHAT_ID)
