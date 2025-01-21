from .__torrent_manager import TorrentManager

__name_mapping = {
    "transmission": "module.torrent_manager.__torrent_manager.TransmissionManager",
    "qbittorrent": "module.torrent_manager.__torrent_manager.QBittorrentManager",
}


def create_manager(client_type: str, host: str, port: int, username: str, password: str, protocol: str = 'http') \
        -> TorrentManager:
    """
    Фабричный метод для создания менеджеров.

    :param client_type: Тип клиента, может быть "transmission" или "qbittorrent".
    :param host: Хост для подключения к торрент-клиенту.
    :param port: Порт для подключения к торрент-клиенту.
    :param username: Имя пользователя для авторизации.
    :param password: Пароль для авторизации.
    :param protocol: Протокол ["http", "httpx"].

    :return: Экземпляр соответствующего менеджера.
    """
    if client_type not in __name_mapping:
        raise ValueError(f"Неизвестный тип клиента: {client_type}")
    module_path, class_name = __name_mapping[client_type].rsplit('.', 1)

    module = __import__(module_path, fromlist=[class_name])
    manager_class = getattr(module, class_name)
    return manager_class(host, port, username, password, protocol)

