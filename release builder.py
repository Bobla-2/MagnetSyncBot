import shutil
import os

# === Настройки ===
SOURCE_DIR = r".\\"  # Папка, которую копируем
DEST_DIR = r"C:\\Users\\savva\\Desktop\\MagnetSyncBot"  # Куда копируем

# Укажи файлы и папки, которые нужно удалить
FILES_TO_DELETE = ["config.py", ".gitignore", "torrents.bd"]  # Файлы, которые удаляем
FOLDERS_TO_DELETE = ["logs_backup", "logs", "доки", ".git", ".idea", "__pycache__"]  # Папки, которые удаляем

def copy_directory(source, destination):
    """Копирует папку полностью."""
    try:
        shutil.copytree(source, destination, dirs_exist_ok=True)
        print(f"✅ Папка успешно скопирована: {destination}")
    except Exception as e:
        print(f"❌ Ошибка при копировании: {e}")

def delete_files_and_folders(target_dir):
    """Удаляет указанные файлы и папки в целевой директории."""
    for root, dirs, files in os.walk(target_dir, topdown=False):
        # Удаление файлов
        for file in files:
            if file in FILES_TO_DELETE:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"🗑️ Удалён файл: {file_path}")
                except Exception as e:
                    print(f"❌ Ошибка удаления файла {file_path}: {e}")

        # Удаление папок
        for folder in dirs:
            if folder in FOLDERS_TO_DELETE:
                folder_path = os.path.join(root, folder)
                try:
                    shutil.rmtree(folder_path)
                    print(f"🗑️ Удалена папка: {folder_path}")
                except Exception as e:
                    print(f"❌ Ошибка удаления папки {folder_path}: {e}")


def zip_folder(folder_path, zip_path):
    """Архивирует указанную папку в ZIP."""
    try:
        shutil.make_archive(zip_path.replace(".zip", ""), 'zip', folder_path)
        print(f"✅ Папка {folder_path} сжата в ZIP: {zip_path}")
    except Exception as e:
        print(f"❌ Ошибка при архивации: {e}")

if __name__ == "__main__":
    copy_directory(SOURCE_DIR, DEST_DIR)  # Копируем папку
    delete_files_and_folders(DEST_DIR)    # Чистим ненужные файлы/папки
    # zip_folder(DEST_DIR, DEST_DIR + '\MagnetSyncBot.zip')
    print("✅ Операция завершена!")
