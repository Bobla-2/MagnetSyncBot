import os


class CreaterSymlinksJellyfin:
    def __init__(self, target_dir: str):
        self.__target_dir = target_dir
        if not os.path.exists(self.__target_dir):
            os.makedirs(self.__target_dir)

    def create_symlinks(self, source_dir: str) -> None:
        """
        Создает символические ссылки на файлы из source_dir в target_dir.
        """
        for root, _, files in os.walk(source_dir):
            for file in files:
                source_file = os.path.join(root, file)
                relative_path = os.path.relpath(source_file, source_dir)
                target_file = os.path.join(self.__target_dir, relative_path)

                media_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.wmv'}
                if os.path.splitext(file)[1].lower() in media_extensions:
                # Создаем папки, если они отсутствуют
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)

                    if not os.path.exists(target_file):
                        os.symlink(source_file, target_file)
                        print(f"Создан симлинк: {target_file} -> {source_file}")
                    else:
                        print(f"Симлинк уже существует: {target_file}")

    def create_symlink(self, source_file: str, file_name: str) -> None:
        """
        Создает символическую ссылку на файл source_file в папке target_dir.
        """
        if not os.path.exists(source_file):
            print(f"Ошибка: файл {source_file} не существует.")
            return

        target_file = os.path.join(self.__target_dir, file_name)

        if not os.path.exists(target_file):
            os.symlink(source_file, target_file)
            print(f"Создан симлинк: {target_file} -> {source_file}")
        else:
            print(f"Симлинк уже существует: {target_file}")






if __name__ == "__main__":
    s = CreaterSymlinksJellyfin("target_dir")
    s.create_symlinks("source_dir")
    s.create_symlink("source_file", "132")