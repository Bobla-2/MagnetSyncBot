# MagnetSyncBot
Телеграмм бот позволяющий находить контент на трекерах, а также управлять загрузками на удаленном клиенте transmission или qB.

## Info
[![Release](https://img.shields.io/github/v/release/Bobla-2/MagnetSyncBot?releases)](https://github.com/Bobla-2/MagnetSyncBot/releases/latest)

## Содержание
- [Использование](#Использование)
- [Использование_Docker](#Использование_Docker)
- [Создание_config_файла](#Создание_config_файла)
- [Список_команд](#Список_команд)
- [Сборка_проекта](#Сборка_проекта)

## Использование
**1) Скачать последний релиз**

[**Скачать**](https://github.com/username/repository/releases/latest/download/MagnetSyncBot.zip)

**2) Установка зависимостей**
```
pip install -r requirements.txt
```
**3) Создать файл config файла**

Алгоритм описан в [Создание_config_файла](#Создание_config_файла)

**4) Запуск**
```
python main.py 
```
Для просмотра дополнительных параметров используйте `-h`


## Использование_Docker

**1) Скачать последний релиз**
```
wget https://github.com/Bobla-2/MagnetSyncBot/releases/latest/download/MagnetSyncBot.zip
```
**2) Распаковать проект**
```
unzip MagnetSyncBot.zip
```
**3) Создать файл конфигурации**

```
sudo nano ./MagnetSyncBot/module/crypto_token/config.py
```

Подробнее в [Создание_config_файла](#Создание_config_файла)

**4) Сборка образа** 
```
docker build -t magnetsyncbot ./MagnetSyncBot/
```
**5-1) Создание контейнера через docker run**
```
docker run -d -p 8080:8080 -p 9091:9091 --name magnetsyncbot magnetsyncbot
```
10811 - порт прокси;
8080 - qBittorrent;
9091 - transmission;

**5-2) Создание контейнера через docker-compose**
```
cd ./MagnetSyncBot && docker compose up -d
```


## Создание_config_файла 
Для работы нужно создать файл "MagnetSyncBot\module\crypto_token\config.py" с методами и переменными:

(Шаблон "MagnetSyncBot\module\crypto_token\config_templ.py")
- `get_token() -> str` (токен от ТГ бота)
- `get_pass_rutreker() -> str` (пароль от рутрекера)
- `get_login_rutreker() -> str` (логин от рутрекера)
- `get_pass_defualt_torent_client() -> str` (пароль для торрент-клиента по умолчанию)

- `proxy: str` = [`"http://host:port"`|`"socks5h://user:password@host:port"`]
- `tornt_cli_host: str` (хост торрент-клиента по умолчанию)
- `tornt_cli_port: int` (порт торрент-клиента по умолчанию)
- `tornt_cli_type: str` (тип торрент-клиента по умолчанию)
- `tornt_cli_login: str` (логин для торрент-клиента по умолчанию)
- `jellyfin: bool` (включение функции генерации symlink)
- `jellyfin_dir: str` (путь куда генерировать symlink)
Подробнее можно прочитать в шаблоне


## Список_команд
Новый интерфейс перешел на кнопки, но команды поддерживаются

 - Для начала: `/start`
 - Для поиска: `/search {РЕСУРС} {НАЗВАНИЕ}`

   РЕСУРС = [None(RuTracker), 1337]
 - Для скачивания: `/download {НОМЕР}`
 - Для просмотра параметров: `/look {НОМЕР}`

### Команды не имеющие аналогов в виде кнопок
 - Для установки кастомного торрент клиента введите:
   `/start {type}:{host}:{port}:{login}:{pass}`
   - type = [qbittorrent, transmission]
   - if host = 'https://' -> port = 443
 - /log - последние 4000 символов лога
 - /last_log - краткая запись последней критической ошибки

## Сборка_проекта
Для сборки проекта существует скрипт, который позволяет создать копию с удалением не нужных файлов/папок
`release builder.py` 

## Команда_проекта
 - ушла спать:/
