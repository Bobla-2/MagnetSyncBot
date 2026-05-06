from abc import ABC, abstractmethod


class ABCTorrentInfo(ABC):
    __slots__ = ()
    """
    Абстрактный базовый класс для объектов, содержащих данные о торренте.
    Определяет интерфейс, который должен быть реализован в конкретных классах.
    """

from abc import ABC, abstractmethod


class ABCTorrentInfo(ABC):
    __slots__ = ()
    """
    Абстрактный базовый класс для объектов, содержащих данные о торренте.
    Определяет интерфейс, который должен быть реализован в конкретных классах.
    """

    @property
    @abstractmethod
    def get_magnet(self) -> str:
        """
        Возвращает магнет-ссылку для торрента.

        Returns:
            str: Магнет-ссылка.
        """
        pass

    @property
    @abstractmethod
    def size(self) -> str:
        """
        Возвращает размер торрента в строковом формате (например, '1.5 GB').

        Returns:
            str: Размер торрента.
        """
        pass

    @property
    @abstractmethod
    def get_other_data(self) -> list:
        pass

    @property
    @abstractmethod
    def short_category(self) -> str | None:
        """Возвращает простую категорию торрента из config.MEDIA_EXTENSIONS"""
        pass

    @property
    @abstractmethod
    def url(self) -> str:
        pass

    @property
    @abstractmethod
    def season(self) -> int:
        pass

    @property
    @abstractmethod
    def qualiti(self) -> str:
        pass

    @property
    @abstractmethod
    def enable_magnet(self) -> bool:
        pass


class ABCTorrenTracker(ABC):
    '''Класс используемый для поиска тореннтов'''
    @abstractmethod
    def get_tracker_list(self, search_request: str) -> list[ABCTorrentInfo]:
        '''
        функция
        :param search_request: поисковой запрос
        :return: List[ABCTorrentInfo] возвращает список датаклассов с информацией о трекерах
        '''
        pass




