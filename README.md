# MagnetSyncBot
Телеграмм бот позволяющий находить контент на ruTracker и 1337x, а также управлять загрузками на удаленном клиенте transmission или qB.

## Info
[![Release](https://img.shields.io/github/v/release/Bobla-2/MagnetSyncBot?releases)](https://github.com/Bobla-2/MagnetSyncBot/releases/latest)

## Содержание
- [Использование](#Использование)
- [Использование_Docker](#Использование_Docker)
- [Настройка_конфигурации](#Настройка_конфигурации)
- [Список_команд](#Список_команд)

## Использование

**1) Установка зависимостей**
```
pip install -r requirements.txt
```
**2) Создать файл настроек**

Алгоритм описан в [Настройка_конфигурации](#Настройка_конфигурации)

**3) Запуск**
```
python main.py 
```
Для просмотра дополнительных параметров используйте `-h`


## Использование_Docker

**1) Создать файл настроек**

Алгоритм описан в [Настройка_конфигурации](#Настройка_конфигурации)

**2) Сборка образа** 
```
docker build -t magnetsyncbot /home/sas/MagnetSyncBot/
```
**3) Создание контейнера**
```
docker run -d -p 10811:10811 -p 8080:8080 -p 9091:9091 --name magnetsyncbot magnetsyncbot
```
10811 - порт прокси;
8080 - qBittorrent;
9091 - transmission;


## Настройка_конфигурации
Для работы нужно создать файл "MagnetSyncBot\module\crypto_token\config.py" с методами и переменными:

(Шаблон "MagnetSyncBot\module\crypto_token\config_templ.py")
- `get_token() -> str` (токен от ТГ бота)
- `get_pass_rutreker() -> str` (пароль от рутрекера)
- `get_login_rutreker() -> str` (логин от рутрекера)
- `get_pass_defualt_torent_client() -> str` (пароль для торрент-клиента по умолчанию)

- `proxy: str` = 'http://127.0.0.1:10809'
- `tornt_cli_host: str` (хост торрент-клиента по умолчанию)
- `tornt_cli_port: int` (порт торрент-клиента по умолчанию)
- `tornt_cli_type: str` (тип торрент-клиента по умолчанию)
- `tornt_cli_login: str` (логин для торрент-клиента по умолчанию)

#### Шифрование

Методы могут использовать шифрование. Для этого можно использовать метод __decrypt_data(key: bytes, data: bytes) из файла crypt_token.py и возвращать его результат

Для генерации key и data нужно использовать файл crypt_token.py

## Список_команд
 - Для начала введите: `/start`
 - Для поиска: `/search {РЕСУРС} {НАЗВАНИЕ}`

   РЕСУРС = [None(RuTracker), 1337]
 - Для скачивания: `/download {НОМЕР}`
 - Для просмотра параметров: `/look {НОМЕР}`
 - Для установки кастомного торрент клиента введите:

   `/start {type}:{host}:{port}:{login}:{pass}`
   - type = [qbittorrent, transmission]
   - if host = 'https://' -> port = 443


## Команда_проекта
 - ушла спать:/
