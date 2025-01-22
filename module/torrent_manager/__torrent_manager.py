from transmission_rpc import Client as TransmissionClient
from qbittorrentapi import Client as QBittorrentClient
from abc import ABC, abstractmethod


class TorrentManager(ABC):
    """Базовый интерфейс для торрент-менеджеров"""

    @abstractmethod
    def __init__(self, host: str, port: int, username: str, password: str, protocol: str):
        """
        Абстрактный метод конструктора.
        :param host: str — Хост для подключения.
        :param port: int — Порт для подключения.
        :param username: str — Имя пользователя.
        :param password: str — Пароль пользователя.
        :param protocol: str — Протокол соединения.
        """
        pass

    @abstractmethod
    def start_download(self, magnet_url: str):
        pass

    @abstractmethod
    def get_progress(self, id: int = None) -> float:
        '''
        :param id: id torrent. default last id
        :return: progress download at 0 to 1
        '''
        pass

    @abstractmethod
    def stop_download(self, id: int = None) -> float:
        pass


class TransmissionManager(TorrentManager):
    def __init__(self, host, port, username, password, protocol='http'):
        self.__client = TransmissionClient(host=host, port=port, username=username, password=password,
                                           protocol=protocol)
        self.__id_last: int = 0

    def start_download(self, magnet_url: str) -> int:
        if magnet_url != "":
            self.__id_last = self.__client.add_torrent(magnet_url).id
            return self.__id_last
        return -1

    def get_progress(self, id: int = None) -> float:
        '''
        :param id: id torrent. default last id
        :return: progress download at 0 to 1
        '''
        if not id:
            id = self.__id_last
        print(f'{id} progress download{self.__client.get_torrent(id).progress / 100}')
        return self.__client.get_torrent(id).progress / 100

    def stop_download(self, id: int = None):
        self.__client.stop_torrent(id)


class QBittorrentManager(TorrentManager):
    def __init__(self, host, port, username, password):
        self.__client = QBittorrentClient(host=host, port=port, username=username, password=password)
        self.__client.auth_log_in()

    def start_download(self, magnet_url: str):
        self.__client.torrents_add(urls=magnet_url)

    def get_progress(self, id: int = None) -> float:
        return -1.

