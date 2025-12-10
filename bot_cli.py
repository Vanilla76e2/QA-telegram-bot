import os
import json
import subprocess
import signal
import sys
import platform
from pathlib import Path

CONFIG_FILE = "config.json"
LOG_DIR = Path("logs")
PID_FILE = Path("bot.pid")

DEFAULT_CONFIG = {
    "BOT_TOKEN": "",
    "WORK_CHAT_ID": 0
}

LOG_DIR.mkdir(exist_ok=True)

# -------- Работа с конфигом --------
def load_config():
    if not os.path.exists(CONFIG_FILE) or os.path.getsize(CONFIG_FILE) == 0:
        save_config(DEFAULT_CONFIG)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def show_config():
    config = load_config()
    print("Текущие настройки:")
    for k, v in config.items():
        print(f"{k}: {v}")

def set_config(key, value):
    config = load_config()
    if key not in config:
        print(f"Ключ {key} не существует")
        return
    if key == "WORK_CHAT_ID":
        value = int(value)
    elif key == "Managers":
        value = value.split(",")
    config[key] = value
    save_config(config)
    print(f"{key} обновлён!")

# -------- Работа с процессом бота --------
def run_bot():
    if PID_FILE.exists():
        print("Бот уже запущен!")
        return

    config = load_config()
    if not config["BOT_TOKEN"] or not config["WORK_CHAT_ID"]:
        print("Не задан BOT_TOKEN или WORK_CHAT_ID!")
        return

    log_file = LOG_DIR / "bot.log"
    print(f"Запускаем бота, логи в {log_file}")

    kwargs = {
        "stdout": open(log_file, "a"),
        "stderr": subprocess.STDOUT,
    }

    # preexec_fn только на Unix
    if platform.system() != "Windows":
        kwargs["preexec_fn"] = os.setsid

    proc = subprocess.Popen([sys.executable, "bot.py"], **kwargs)
    PID_FILE.write_text(str(proc.pid))

def stop_bot():
    if not PID_FILE.exists():
        print("Бот не запущен!")
        return

    pid = int(PID_FILE.read_text())
    print(f"Останавливаем процесс {pid}")

    try:
        if platform.system() == "Windows":
            os.kill(pid, signal.SIGTERM)
        else:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
    except ProcessLookupError:
        print("Процесс уже не существует")
    finally:
        PID_FILE.unlink()
        print("Бот остановлен")

def restart_bot():
    stop_bot()
    run_bot()

def show_logs(lines=50):
    log_file = LOG_DIR / "bot.log"
    if not log_file.exists():
        print("Логи отсутствуют")
        return
    with open(log_file) as f:
        content = f.readlines()
    print("".join(content[-lines:]))

# -------- CLI --------
def main():
    while True:
        print("\n=== Telegram Bot CLI ===")
        print("1. Показать настройки")
        print("2. Изменить настройку")
        print("3. Запустить бота")
        print("4. Остановить бота")
        print("5. Перезапустить бота")
        print("6. Показать логи")
        print("0. Выход")

        choice = input("> ").strip()
        if choice == "1":
            show_config()
        elif choice == "2":
            key = input("Ключ: ").strip()
            value = input("Новое значение: ").strip()
            set_config(key, value)
        elif choice == "3":
            run_bot()
        elif choice == "4":
            stop_bot()
        elif choice == "5":
            restart_bot()
        elif choice == "6":
            show_logs()
        elif choice == "0":
            print("Выход")
            break
        else:
            print("Неверный выбор")

if __name__ == "__main__":
    main()
