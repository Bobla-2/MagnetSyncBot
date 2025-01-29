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
    def stop_download(self, id: int):
        '''
        :param id: id torrent.
        '''
        pass

    @abstractmethod
    def get_path(self, id: int) -> str:
        '''
        :param id: id torrent. default last id
        :return: path
        '''
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
        return 0

    def get_progress(self, id: int = None) -> float:
        '''
        :param id: id torrent. default last id
        :return: progress download at 0 to 1
        '''
        if not id:
            id = self.__id_last
        progress = self.__client.get_torrent(id).progress / 100
        print(f'{id} progress download{progress}')
        return progress

    def stop_download(self, id: int):
        self.__client.stop_torrent(id)

    def get_path(self, id: int) -> str:
        '''
        :param id: id torrent. default last id
        :return: path
        '''
        if not id:
            id = self.__id_last
        dir_ = self.__client.get_torrent(id).download_dir
        print(f'{id} dir download{dir_}')
        return dir_


class QBittorrentManager(TorrentManager):
    def __init__(self, host, port, username, password, protocol='http'):
        self.__client = QBittorrentClient(host=f"{protocol}://{host}:{port}", username=username, password=password)
        self.__client.auth_log_in()
        self.__id_last: str = ""

    def start_download(self, magnet_url: str):
        if magnet_url != "":
            self.__client.torrents_add(urls=magnet_url)
            # Получаем последний добавленный торрент
            torrents = self.__client.torrents_info(sort="added_on", reverse=True)
            if torrents:
                self.__id_last = torrents[0].hash
                return self.__id_last
        return ""

    def get_progress(self, id: str = None) -> float:
        if not id:
            id = self.__id_last
        if id:
            torrents = self.__client.torrents_info(hashes=id)
            if torrents:
                progress = torrents[0].progress
                print(f'{id} progress download: {progress}')
                return progress
        return 0.0

    def stop_download(self, id: str):
        '''
        :param id: Хэш (идентификатор) торрента. По умолчанию используется последний добавленный торрент.
        '''
        if not id:
            id = self.__id_last
        if id:
            self.__client.torrents_pause(hashes=id)

    def get_path(self, id: int) -> str:
        '''
        :param id: id torrent. default last id
        :return:
        '''
        if not id:
            id = self.__id_last
        dir_ = self.__client.torrents_info(torrent_hash=id)[0].save_path
        print(f'{id} dir download{dir_}')
        return dir_

