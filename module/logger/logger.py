import os
import shutil
from datetime import datetime
from module.crypto_token import config

def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


@singleton
class SimpleLogger:
    def __init__(self, log_dir="logs", backup_dir="logs_backup", end_log_marker="END_LOG"):
        self.log_dir = log_dir
        self.backup_dir = backup_dir
        self.end_log_marker = end_log_marker
        self.log_file = os.path.join(log_dir, "current_log.txt")

        # Создаем директории, если они не существуют
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

        # Проверяем последний лог
        self._check_last_log()

    def _check_last_log(self):
        # Проверяем наличие текущего лога
        if os.path.exists(self.log_file):
            last_line = None
            with open(self.log_file, "r") as file:
                lines = file.readlines()
                if lines:
                    last_line = lines[-1].strip() if file else ""

            # Если последний лог не завершён, сохраняем его в архив
            if last_line and last_line.split()[-1] != self.end_log_marker:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(self.backup_dir, f"log_backup_{timestamp}.txt")
                shutil.move(self.log_file, backup_file)
        with open(self.log_file, "w") as file:
            file.write("")

    def log(self, message: str):
        with open(self.log_file, "a") as file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                file.write(f"{timestamp} - {message}\n")
            except:
                print("ошибка логирования: не удалось записать лог в файл")
            print(message)

    def get_log_text(self) -> str:
        n = 8090
        with open(self.log_file, "rb") as f:  # открываем в бинарном режиме
            f.seek(0, 2)  # ставим указатель в конец файла
            size = f.tell()  # размер файла
            f.seek(max(size - n, 0), 0)  # сдвигаем на size-n или на начало, если файл меньше
            data = f.read()

        text = data.decode(encoding=config.log_file_encoding, errors="ignore")
        return text



    def end_log(self):
        # Записываем маркер завершения
        self.log(self.end_log_marker)
