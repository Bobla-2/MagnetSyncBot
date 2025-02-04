import os
from module.crypto_token import config


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


@singleton
class CreaterSymlinksJellyfin:
    def __select_category_folder(self, category) -> str | None:
        for categories, folder_path, condition, _ in config.MEDIA_EXTENSIONS:
            if condition == "==":
                if category in categories:
                    return folder_path
            elif condition == "in":
                if any(cat in category for cat in categories):
                    return folder_path
        return None

    def create_symlink(self, original_path: str, category):
        """Создает симлинк в Jellyfin для файла, заменяя /download/ на /mnt/nas_downloads/"""
        relative_path = original_path.split(config.TORRENT_FOLDER, 1)[1]  # Берем всё после /download/
        category_folder = self.__select_category_folder(category)
        full_path_category = os.path.join(config.JELLYFIN_PATH, category_folder)
        target_file = os.path.join(full_path_category, relative_path)

        if os.path.exists(target_file):
            print(f"Симлинк уже существует: {target_file}")
            return
        try:
            os.symlink(original_path, target_file)
            print(f"Симлинк создан: {original_path} -> {target_file}")
        except Exception as e:
            print(f"Ошибка создания симлинка: {e}")


if __name__ == "__main__":
    s = CreaterSymlinksJellyfin()
    s.create_symlink("/home/user/some/path/download/хуйня/", 'Аниме (SD Video)')