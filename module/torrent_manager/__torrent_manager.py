from transmission_rpc import Client as TransmissionClient
from qbittorrentapi import Client as QBittorrentClient
from abc import ABC, abstractmethod
import time
from module.crypto_token import config
from module.logger.logger import SimpleLogger


class ActiveTorrentsInfo:
    """_"""
    __slots__ = ('num', 'name', 'status', 'progress', 'id')

    def __init__(self, num, name, status, progress, id):
        self.num = num
        self.name = name
        self.status = status
        self.progress = progress
        self.id = id


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
    def start_download(self, magnet_url: str, subfolder: str = '') -> str | int:
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

    @abstractmethod
    def get_list_active_torrents(self) -> list[ActiveTorrentsInfo]:
        pass

    @abstractmethod
    def delete_torrent(self, id: int) -> None:
        pass


class TransmissionManager(TorrentManager):
    def __init__(self, host, port, username, password, protocol='http'):
        self.__client = TransmissionClient(host=host, port=port, username=username, password=password,
                                           protocol=protocol)
        self.__id_last: int = 0
        time.sleep(1)
        self.__default_dir = config.TORRENT_FOLDER

    def start_download(self, magnet_url: str, subfolder: str = "") -> int:
        if magnet_url != "":
            if subfolder:
                download_dir = f"{self.__default_dir}/{subfolder}"[:-1].replace('//', '/')
            else:
                download_dir = self.__default_dir

            self.__id_last = self.__client.add_torrent(torrent=magnet_url, download_dir=download_dir).id
            self.__client.start_torrent(self.__id_last)
            return self.__id_last
        return 0

    def get_progress(self, id: int = None) -> float:
        '''
        :param id: id torrent. default last id
        :return: progress download at 0 to 1
        '''
        # self.get_path()
        if not id:
            id = self.__id_last
        progress = self.__client.get_torrent(id).progress / 100
        print(f'{id} progress download: {progress}')
        return progress

    def stop_download(self, id: int):
        self.__client.stop_torrent(id)

    def get_list_active_torrents(self) -> list[ActiveTorrentsInfo]:
        torrents = self.__client.get_torrents()
        out_list = []
        torrents_sorted = sorted(torrents, key=lambda t: t.added_date, reverse=True)
        for num, torrent in enumerate(torrents_sorted):
            out_list.append(ActiveTorrentsInfo(num, torrent.name, torrent.status, f"{torrent.progress:.1f}%", torrent.id))
        return out_list

    def delete_torrent(self, id: int):
        SimpleLogger().log(f"TransmissionManager: Удаление торрента: {id}")
        try:
            self.__client.remove_torrent(
                ids=id,
                delete_data=True
            )
        except Exception as e:
            SimpleLogger().log(f"TransmissionManager: Ошибка при удалении торрента: {e}")

    def get_path(self, id: int = None) -> str:
        '''
        :param id: id torrent. default last id
        :return: path
        '''
        if not id:
            id = self.__id_last
        torents = self.__client.get_torrent(id)
        dir_ = f"{torents.download_dir}/{torents.name}".replace('//', '/')
        print(f'{id} dir download  {dir_}')
        return dir_


class QBittorrentManager(TorrentManager):
    def __init__(self, host, port, username, password, protocol='http'):
        self.__client = QBittorrentClient(host=f"{protocol}://{host}:{port}", username=username, password=password,
                                          REQUESTS_ARGS={'timeout': (1, 5)})
        self.__client.auth_log_in()
        self.__id_last: str = ""
        self.__default_dir = config.TORRENT_FOLDER


    def start_download(self, magnet_url: str, subfolder: str = '') -> str:
        if magnet_url != "":
            if subfolder:
                download_dir = f"{self.__default_dir}/{subfolder}".replace('//', '/')
            else:
                download_dir = self.__default_dir
            self.__client.torrents_add(urls=magnet_url, savepath=download_dir)

            time.sleep(0.1)
            torrents = self.__client.torrents_info()

            magnet_url = (magnet_url.replace('+', '%20').
                          replace(':', '%3a').
                          replace('/', '%2f').lower())
            torrent_hash = None
            for t in torrents:
                tor_magnet_utl = t.magnet_uri.replace('+', '%20').replace(':', '%3a').replace('/', '%2f').lower()[:100]
                if (tor_magnet_utl == magnet_url[:100]):
                    torrent_hash = t.hash
                    break

            self.__client.torrents_resume(hashes=torrent_hash)
            return torrent_hash
        return ""

    def get_progress(self, id: str = None) -> float:
        print(self.get_path(id))
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
        if not id:
            return

        try:
            if hasattr(self.__client, 'torrents_stop'):
                self.__client.torrents_stop(hashes=id)
            elif hasattr(self.__client, 'torrents_pause'):
                self.__client.torrents_pause(hashes=id)
            else:
                SimpleLogger().log("Невозможно остановить торрент — нет подходящего метода.")
        except Exception as e:
            SimpleLogger().log(f"Ошибка при остановке торрента: {e}")

    def get_path(self, id: str = None) -> str:
        '''
        :param id: id torrent. default last id
        :return:
        '''
        if not id:
            id = self.__id_last
        dir_ = self.__client.torrents_info(torrent_hashes=id)
        dir_ = dir_[0].content_path
        print(f'{id} dir download  {dir_}')
        return dir_

    def get_list_active_torrents(self) -> list[ActiveTorrentsInfo]:
        torrents = self.__client.torrents_info()
        out_list = []
        torrents_sorted = sorted(torrents, key=lambda t: t.added_on, reverse=True)
        for num, torrent in enumerate(torrents_sorted):
            out_list.append(
                ActiveTorrentsInfo(str(num), str(torrent.name), str(torrent.state), f"{torrent.progress*100:.1f}%", torrent.hash))
        return out_list

    def delete_torrent(self, torrent_hash: str):
        SimpleLogger().log(f"QBittorrentManager: Удалении торрента: {torrent_hash}")
        try:
            self.__client.torrents_pause(torrent_hashes=torrent_hash)

            self.__client.torrents_delete(
                delete_files=True,
                torrent_hashes=torrent_hash
            )
        except Exception as e:
            SimpleLogger().log(f"QBittorrentManager: Ошибка при удалении торрента: {e}")


