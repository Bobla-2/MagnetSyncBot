import os
from module.crypto_token import config
import paramiko
import re
import asyncio
def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


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

    def create_symlink(self, original_path, custam_name: str, progress_value, id: int | str):
        self.task[str(id)] = asyncio.create_task(self.__start_create_symlink(original_path, custam_name, progress_value))

    async def __start_create_symlink(self, original_path, custam_name: str, progress_value):
        while progress_value() < 1.:
            await asyncio.sleep(5)
        await asyncio.sleep(5)
        print("Генерация симлмнка")
        original_path = original_path()
        path, orig_name = original_path.rsplit("/", 1)
        target_path = f'{path.replace(config.TORRENT_FOLDER[:-1], config.JELLYFIN_PATH[:-1])}/{custam_name}'
        split_orig_name = orig_name.rsplit(".", 1)
        if len(split_orig_name) == 2:
            target_path = f'{target_path}.{split_orig_name[1]}'
        original_path = original_path.replace('//', '/')
        target_path = target_path.replace('//', '/')

        target_path = re.sub(r'[:*?"<>|]', '', target_path)
        relative_path = os.path.relpath(original_path, start=os.path.dirname(target_path))
        relative_path = re.sub(r'[:*?"<>|]', '', relative_path)
        self.__generator.create_symlink(relative_path, target_path)

    def stop_task(self, id: str | int):
        """Останавливаем задачу"""
        if (tsk := self.task.pop(str(id), None)):  # Удаляем из словаря и отменяем
            tsk.cancel()
        else:
            print(f"Задача {id} не найдена!")


@singleton
class CreaterSymlinks:
    def __init__(self):
        self.client = True
    def create_symlink(self, original_path: str, target_file: str):
        if os.path.exists(target_file):
            print(f"Симлинк уже существует: {target_file}")
            return
        try:
            os.symlink(original_path, target_file)
            print(f"Симлинк создан: {original_path} -> {target_file}")
        except Exception as e:
            print(f"Ошибка создания симлинка: {e}")



@singleton
class SSHSymlinkCreator:
    def __init__(self):
        self.client = None

    def connect(self):
        """Устанавливает SSH-соединение."""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(
                config.SYMLINK_HOST,
                port=config.SYMLINK_PORT,
                username=config.SYMLINK_LIGIN,
                password=config.SYMLINK_PASS,
            )
        except:
            self.client = None

    def create_symlink(self, relative_path: str, targer_path):
        """Создает символическую ссылку на удаленном сервере."""
        if not self.client:
            print("SSH-соединение не установлено")
            return

        command = f'ln -s "{relative_path}" "{targer_path}"'.replace('\\\\', '\\').replace('\\', '/')
        command_mkdir = f'mkdir -p "{targer_path.rsplit("/", 1)[0]}"'.replace('\\\\', '\\').replace('\\', '/')

        stdin, stdout, stderr = self.client.exec_command(command_mkdir)
        error = stderr.read().decode()
        if error:
            print(f"Ошибка при создании mkdir: {error}")

        stdin, stdout, stderr = self.client.exec_command(command, get_pty=True)
        stdout.channel.set_combine_stderr(True)

        # Чтение вывода и ошибок в одном потоке
        output = stdout.read().decode('utf-8')
        print(command)
        print(output)
        # return stdout.read().decode().strip()

    def close(self):
        """Закрывает SSH-соединение."""
        if self.client:
            self.client.close()
            self.client = None

# Пример использования
if __name__ == "__main__":
    print(f'{config.JELLYFIN_PATH}{"/download/folder/".replace(config.TORRENT_FOLDER, "")}{"custam_name"}')