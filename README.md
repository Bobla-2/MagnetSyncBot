# MagnetSyncBot
Телеграмм бот позволяющий находить контент на ruTracker и управлять загрузками на удаленном клиенте transmission или qb.

## Содержание
- [Работа_с_исходным_кодом](#Работа_с_исходным_кодом)

## Работа_с_исходным_кодом
Для работы нужно создать файл "MagnetSyncBot\module\crypto_token\config.py" с методами и переменными:
- get_token() -> str (токен для ТГ бота)
- get_pass_rutreker() -> str (логин для рутрекера)
- get_login_rutreker() -> str (логин для рутрекера)
- get_pass_defualt_torent_client() -> str (по умолчанию пытается использовать transmission с логином transmission)
- proxy: str = 'http://127.0.0.1:10809'

Методы могут использовать шифрование. Для этого можно использовать метод __decrypt_data(key: bytes, data: bytes) из файла crypt_token.py и возвращать его результат

Для генерации key и data нужно использовать файл crypt_token.py

## Команда проекта
 - ушла спать:/
