from abc import ABC, abstractmethod


class AbstractTorrentInfo(ABC):
    __slots__ = ()
    """
    Абстрактный базовый класс для объектов, содержащих данные о торренте.
    Определяет интерфейс, который должен быть реализован в конкретных классах.
    """

    @property
    @abstractmethod
    def get_magnet(self) -> str:
        """Ссылка на магнет торрента."""
        pass

    @property
    @abstractmethod
    def get_other_data(self) -> str:
        """Другие данные торрента."""
        pass

    @property
    @abstractmethod
    def full_info(self) -> str:
        """Полная информация о торренте в формате .md."""
        pass

    @property
    @abstractmethod
    def id_torrent(self) -> str:
        pass

    @id_torrent.setter
    @abstractmethod
    def id_torrent(self, id_: str | int):
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Размер торрента (например, в MB, GB)."""
        pass

