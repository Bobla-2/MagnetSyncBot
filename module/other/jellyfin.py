import os
from module.crypto_token import config
import paramiko
import re
import time
import threading
from module.logger.logger import SimpleLogger
from module.other.singleton import singleton


task_lock = threading.RLock()


VIDEO_EXTS = {
    "mkv", "mp4", "avi", "mov", "wmv",
    "flv", "webm", "m4v", "mpg", "mpeg"
}

@singleton
class CreaterSymlinkManager:
    def __init__(self):
        self.task = {}
        if config.SYMLINK_IS_SSH:
            self.__generator = SSHSymlinkCreator()
            self.__generator.connect()
        else:
            self.__generator = CreaterSymlinks()

    @property
    def is_connect(self) -> bool:
        if self.__generator.client:
            return True
        return False

    def create_symlink(self, original_path, custam_name, progress_value, id, category):
        stop_event = threading.Event()

        def runner():
            try:
                self.__start_create_symlink(
                    original_path,
                    custam_name,
                    progress_value,
                    category,
                    stop_event
                )
            except Exception as e:
                SimpleLogger().log(f"[Symlink] error: {e}")
            finally:
                with task_lock:
                    self.task.pop(str(id), None)
                SimpleLogger().log(f"[Symlink] task {id} finished")

        thread = threading.Thread(target=runner, daemon=True)
        with task_lock:
            self.task[str(id)] = {
                "thread": thread,
                "stop_event": stop_event
            }

        thread.start()


    def __start_create_symlink(self, original_path, custam_name: str, progress_value, category: str, stop_event) -> None:
        while progress_value() < 1.:
            if stop_event.is_set():
                SimpleLogger().log("[CreaterSymlinkManager] : Остановка задачи")
                return
            time.sleep(5)
        time.sleep(5)
        SimpleLogger().log("[CreaterSymlinkManager] : Генерация симлмнка")
        original_path = original_path()
        path, orig_name = original_path.rsplit("/", 1)
        jellyfin_dir = config.JELLYFIN_FOLDER_OTHER
        for me in config.MEDIA_EXTENSIONS:
            if me[3] == category:
                jellyfin_dir = me[4]
                break
        target_path = f'{jellyfin_dir}/{custam_name}'
        split_orig_name = orig_name.rsplit(".", 1)
        if len(split_orig_name) >= 2:
            ext = split_orig_name[1].lower()
            if ext in VIDEO_EXTS and category in ["cinema", "anime"]:
                target_path = f"{target_path}/{custam_name}.{ext}"
            else:
                pass


            # if category == "cinema":
            #     target_path = f'{target_path}/{custam_name}'
            # if ext and len(ext) <= 5 and ext[0].isalpha() and ext.isalnum():
            #     target_path = f'{target_path}.{ext}'
        original_path = original_path.replace('//', '/').replace('\\', '/')
        target_path = target_path.replace('//', '/').replace('\\', '/')

        target_path = re.sub(r'[:*?"<>|]', '', target_path)
        relative_path = os.path.relpath(original_path, start=os.path.dirname(target_path))
        relative_path = re.sub(r'[:*?"<>|]', '', relative_path)
        self.__generator.create_symlink(relative_path, target_path)

    def stop_task(self, id):
        with task_lock:
            task = self.task.get(str(id))
        if task:
            task["stop_event"].set()
        else:
            print(f"Задача {id} не найдена!")


@singleton
class CreaterSymlinks:
    def __init__(self):
        self.client = True
    def create_symlink(self, original_path: str, target_file: str):
        if os.path.lexists(target_file):
            SimpleLogger().log(f"[CreaterSymlinks] : Симлинк уже существует: {target_file}")
            return
        try:
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            os.symlink(original_path, target_file)
            SimpleLogger().log(f"[CreaterSymlinks] : Симлинк создан: {target_file} -> {original_path}")
        except Exception as e:
            SimpleLogger().log(f"[CreaterSymlinks] : Ошибка создания симлинка: {e}")



@singleton
class SSHSymlinkCreator:
    def __init__(self):
        self.client = None

    def connect(self):
        """Устанавливает SSH-соединение."""
        self.client = paramiko.SSHClient()
        SimpleLogger().log(f"[SSHSymlinkCreator] : Устанавливает SSH-соединение. SSHSymlinkCreator")
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(
                config.SYMLINK_HOST,
                port=config.SYMLINK_PORT,
                username=config.SYMLINK_LOGIN,
                password=config.SYMLINK_PASS,
            )
            SimpleLogger().log(f"[SSHSymlinkCreator] : SSH-соединение установленно")
        except:
            self.client = None
            SimpleLogger().log("[SSHSymlinkCreator] : SSH-соединение не установлено")

    def create_symlink(self, relative_path: str, targer_path):
        """Создает символическую ссылку на удаленном сервере."""
        if not self.client:
            SimpleLogger().log("[SSHSymlinkCreator] : SSH-соединение не установлено")
            return

        command = f'ln -s "{relative_path}" "{targer_path}"'.replace('\\\\', '\\').replace('\\', '/')
        command_mkdir = f'mkdir -p "{targer_path.rsplit("/", 1)[0]}"'.replace('\\\\', '\\').replace('\\', '/')

        stdin, stdout, stderr = self.client.exec_command(command_mkdir)
        error = stderr.read().decode()
        if error:
            SimpleLogger().log(f"[SSHSymlinkCreator] : Ошибка при создании mkdir: {error}")

        stdin, stdout, stderr = self.client.exec_command(command, get_pty=True)
        stdout.channel.set_combine_stderr(True)

        # Чтение вывода и ошибок в одном потоке
        output = stdout.read().decode('utf-8')
        SimpleLogger().log(f"[SSHSymlinkCreator] : {command}")
        SimpleLogger().log(f"[SSHSymlinkCreator] : {output}")
        # return stdout.read().decode().strip()

    def close(self):
        """Закрывает SSH-соединение."""
        if self.client:
            self.client.close()
            self.client = None

# Пример использования
if __name__ == "__main__":
    original_path = "/srv/dev-disk-by-uuid-a8856494-378f-4839-8243-5aa883ea0730/C/download/1_cinema/Arcane.S01.WEBDL.1080p.Rus.Eng"
    custam_name = "name2"
    category = "cinema"
    path, orig_name = original_path.rsplit("/", 1)
    for me in config.MEDIA_EXTENSIONS:
        if me[3] == category:
            dir = me[4]
            break
    target_path = f'{config.JELLYFIN_FOLDER_OTHER}/{custam_name}'
    split_orig_name = orig_name.rsplit(".", 1)
    if len(split_orig_name) >= 2:
        ext = split_orig_name[1]
        if category == "cinema":
            target_path = f'{target_path}/{custam_name}'
        if ext and len(ext) <= 5 and ext[0].isalpha() and ext.isalnum():
            target_path = f'{target_path}.{ext}'
    original_path = original_path.replace('//', '/').replace('\\', '/')
    target_path = target_path.replace('//', '/').replace('\\', '/')

    target_path = re.sub(r'[:*?"<>|]', '', target_path)
    relative_path = os.path.relpath(original_path, start=os.path.dirname(target_path))
    relative_path = re.sub(r'[:*?"<>|]', '', relative_path)

#     "-by-uuid-a8856494-378f-4839-8243-5aa883ea0730/C/downloads/1_cinema/Arcane.S01.WEBDL.1080p.Rus.Eng
# [SSHSymlinkCreator] : ln -s "../../../../../downloads/1_cinema/Arcane.S01.WEBDL.1080p.Rus.Eng" "/srv/dev-disk-by-uuid-a8856494-378f-4839-8243-5aa883ea0730/C/DLNA/1_cinema/Arcane League of Legends/Season 01/Arcane League of Legends/Season 01.Eng"
# [SSHSymlinkCreator] : "