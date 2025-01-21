# MagnetSyncBot
Телеграмм бот позволяющий находить контент на ruTracker и управлять загрузками на удаленном клиенте transmission или qb.

## Содержание
- [Работа_с_исходным_кодом](#Работа_с_исходным_кодом)

## Работа_с_исходным_кодом
Для работы нудно создать файл "MagnetSyncBot\module\crypto_token\config.py" с методами:
- get_token() (токен для ТГ бота)
- get_pass_rutreker() (логин для рутрекера)
- get_login_rutreker() (логин для рутрекера)
- get_pass_defualt_torent_client() (по умолчанию пытается использовать transmission с логином transmission)
Методы должны вызывать метод __decrypt_data(key: bytes, data: bytes) из файла crypt_token.py и возвращать ее результат

Для генерации key и data нужно использовать файл crypt_token.py

## Команда проекта
 - ушла спать:/
