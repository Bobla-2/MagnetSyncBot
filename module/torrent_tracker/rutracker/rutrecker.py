import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from module.torrent_tracker.rutracker.rutracker_api.main import RutrackerApi
import time
import module.crypto_token.config as config
from module.torrent_tracker.TorrentInfoBase import ABCTorrentInfo, ABCTorrenTracker
from module.logger.logger import SimpleLogger
import bencodepy
import hashlib
import urllib.parse
from module.other.singleton import singleton
from threading import RLock
import re


SEASON_RE = re.compile(
    r'(?:'
    r'(?:тв|tv)\s*-?\s*(\d{1,2})'   # ТВ-02, ТВ2, TV 03
    r'|'
    r'season\s*(\d{1,2})'          # Season 01
    r')',
    re.IGNORECASE
)

def _retries_retry_operation(func, *args, retries: int = 2, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Попытка {attempt + 1} из {retries}. Ошибка сети: ПОДКЛЮЧЕНИЯ Rutracker {e}.")
            time.sleep(0.3)
    print(f"Не удалось загрузить RutrackerApi после {retries} попыток.")
    return None


class TorrentInfo(ABCTorrentInfo):
    """
    Класс объекта торрента содержащего все данные о торренте

    имеет несколько @property, берущих данные со страници рутрекера через парсер RutrackerParserPage
    """
    __slots__ = ('__category', '__name', '__year', '__url', '__size_', '__parser', '__id_torrent', '__forum_name', '__short_categories', '__other_data')

    def __init__(self, category: str = '',
                 name: str = None,
                 year: str = None,
                 url: str = None,
                 forum_name: str = None,
                 size: float = 0.):

        self.__forum_name = forum_name
        self.__category = category
        self.__name = name
        self.__year = year
        self.__url = url
        self.__parser = RutrackerParserPage(self.__url)
        self.__id_torrent = None
        self.__short_categories = ''
        self.__other_data = None
        self.__size_ = f'{size} MB' if size < 800. else f'{round(size / 1024, 2)} GB'

    @property
    def name(self) -> str:
        return f"{self.__name}"

    @property
    def size(self) -> str:
        return self.__size_

    @property
    def get_magnet(self) -> str:
        # magnet = self.__parser.get_magnet_link_on_file()
        return self.__parser.get_magnet_link()

    @property
    def get_other_data(self) -> list:
        if self.__other_data is None:
            data = self.__parser.get_other_data()
            data = [["Вес" , self.__size_], ["Категория", self.__category]] + data
            self.__other_data = data
        return self.__other_data

    @property
    def id_torrent(self) -> str:
        return self.__id_torrent

    @id_torrent.setter
    def id_torrent(self, id_: str | int):
        self.__id_torrent = id_

    @property
    def short_category(self) -> str | None:
        if not self.__short_categories:
            for me in config.MEDIA_EXTENSIONS:
                if me[2] == "==":
                    if self.__category in me[0]:
                        self.__short_categories = me[3]
                elif me[2] == "in":
                    if any(cat in self.__category for cat in me[0]):
                        self.__short_categories = me[3]

            if not self.__short_categories:
                self.__short_categories = "other"
        return self.__short_categories


    @property
    def season(self) -> int:
        m = SEASON_RE.search(self.__name)
        return int(m.group(1) or m.group(2)) if m else 1

    @property
    def qualiti(self) -> str:
        title = f"{self.__name}"

        if self.short_category == "music":
            s = (title or "").lower()

            patterns = [
                r'\bflac\b',
                r'\bmp3\b',
                r'\baac\b',
                r'\bogg\b',
                r'\bopus\b',
                r'\bwav\b',
                r'\balac\b',
                r'\bm4a\b',
                r'\baiff\b',
                r'\bwma\b',
            ]

            for pattern in patterns:
                m = re.search(pattern, s, re.IGNORECASE)
                if m:
                    return m.group(0).upper()
        if self.short_category == "cinema" or self.short_category == "anime":
            s = (title or "").lower()

            patterns = [
                r'\bbdremux\b',
                r'\bbdrip\b',
                r'\bbluray\b',
                r'\bweb[-\s]?dl\b',
                r'\bweb[-\s]?rip\b',
                r'\bhdtv\b',
                r'\bdvdrip\b',
                r'\bdvd\b',
                r'\bts\b',
                r'\btc\b',
                r'\bcamrip\b',
                r'\bcam\b',
                r'\bweb[-\s]?dlrip\b',
                r'\bweb[-\s]?dlremux\b',
            ]
            for pattern in patterns:
                m = re.search(pattern, s, re.IGNORECASE)
                if m:
                    return m.group(0).upper()
        return ""

    @property
    def url(self) -> str:
        return self.__url

    @property
    def enable_magnet(self) -> bool:
        return True



@singleton
class Rutracker(ABCTorrenTracker):
    """
    Класс (абстракция на _Rutracker) для инициализации использует данные из crypto_token.config

    добавляет retry_operation при использовании всех функций
    в случае неудачи возвращает список с TorrentInfo содержащим сообщение об ошибке в поле 'name'
    """
    def __init__(self):
        if config.UI_MODE.lower() == "web":
            self.lock = RLock()
        SimpleLogger().log("[Rutracker] : start init")
        self.__rutracker = _retries_retry_operation(_Rutracker,
                                                    username=config.RUTRACKER_LOGIN,
                                                    password=config.RUTRACKER_PASS,
                                                    proxy=config.proxy)

        if not self.__rutracker:
            SimpleLogger().log("[Rutracker] : error init")
        else:
            SimpleLogger().log("[Rutracker] : end init")


    def get_tracker_list(self, search_request: str) -> list[ABCTorrentInfo]:
        if config.UI_MODE.lower() == "web":
            with self.lock:
                if self.__rutracker:
                    list_ = _retries_retry_operation(self.__rutracker.get_search_list, search_request, 1)
                    if list_:
                        return list_
                    else:
                        return [TorrentInfo(name="Ошибка поиска. Попробуйте снова")]
                else:
                    self.__init__()
                    return [TorrentInfo(name="Ошибка подключений к рутрекеру. Попробуйте ввести запрос заново")]
        else:
            if self.__rutracker:
                list_ = _retries_retry_operation(self.__rutracker.get_search_list, search_request, 1)
                if list_:
                    return list_
                else:
                    return [TorrentInfo(name="Ошибка поиска. Попробуйте снова")]
            else:
                self.__init__()
                return [TorrentInfo(name="Ошибка подключений к рутрекеру. Попробуйте ввести запрос заново")]




if __name__ == '__main__':
    p = Rutracker().get_tracker_list("Повелитель тайн")
    print(p[0].get_magnet, p[0].size, p[0].get_other_data)


