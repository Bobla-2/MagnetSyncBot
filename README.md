# MagnetSyncBot
Телеграмм бот позволяющий находить контент на ruTracker и 1337x, а также управлять загрузками на удаленном клиенте transmission или qB.

## Info
[![Release](https://img.shields.io/github/v/release/Bobla-2/MagnetSyncBot?releases)](https://github.com/Bobla-2/MagnetSyncBot/releases/latest)

## Содержание
- [Использование](#Использование)
- [Использование_Docker](#Использование_Docker)
- [Работа_с_исходным кодом](#Работа_с_исходным_кодом)
- [Список_команд](#Список_команд)

## Использование

**1) Установка зависимостей**
```
pip install -r requirements.txt
```
**2) Создать файл настроек**

Алгоритм описан в [Работа_с_исходным_кодом](#Работа_с_исходным_кодом)

**3) Запуск**
```
python main.py {proxy/None}
```
Proxy по умолчанию http://127.0.0.1:10809 

## Использование_Docker

**1) Создать файл настроек**

Алгоритм описан в [Работа_с_исходным_кодом](#Работа_с_исходным_кодом)

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


## Работа_с_исходным_кодом
Для работы нужно создать файл "MagnetSyncBot\module\crypto_token\config.py" с методами и переменными:
- `get_token() -> str` (токен для ТГ бота)
- `get_pass_rutreker() -> str` (логин для рутрекера)
- `get_login_rutreker() -> str` (логин для рутрекера)
- `get_pass_defualt_torent_client() -> str` (по умолчанию пытается использовать transmission с логином transmission)
- `proxy: str` = 'http://127.0.0.1:10809'

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
