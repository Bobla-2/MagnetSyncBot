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
from urllib.parse import quote
from typing import List, Optional
from bs4 import BeautifulSoup, Tag
import requests


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
    __slots__ = ('__category', '__leeches', '__seeds', '__name', '__year', '__url', '__size_', '__parser', '__id_torrent', '__forum_name', '__short_categories', '__other_data')

    def __init__(self, session,
                 category: str = '',
                 name: str = None,
                 year: str = None,
                 url: str = None,
                 forum_name: str = None,
                 seeds: str = None,
                 leeches: str = None,
                 size: str = None,):
        self.__seeds = seeds
        self.__leeches = leeches
        self.__forum_name = forum_name
        self.__category = category
        self.__name = name
        self.__year = year
        self.__url = url
        self.__parser = RutorParserPage(url, session)
        self.__id_torrent = None
        self.__short_categories = ''
        self.__other_data = None
        self.__size_ = size

    @property
    def name(self) -> str:
        return f"{self.__name}"

    @property
    def size(self) -> str:
        return self.__size_

    @property
    def get_magnet(self) -> str:
        magnet = self.__parser.get_magnet_link()
        # return self.__parser.get_magnet_link()
        return magnet

    @property
    def get_other_data(self) -> list:
        if self.__other_data is None:
            # data = self.__parser.get_other_data()
            data = []
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
        # if self.short_category == "music":
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
        # if self.short_category == "cinema" or self.short_category == "anime":
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



# @singleton
# class Rutracker(ABCTorrenTracker):
#     """
#     Класс (абстракция на _Rutracker) для инициализации использует данные из crypto_token.config
#
#     добавляет retry_operation при использовании всех функций
#     в случае неудачи возвращает список с TorrentInfo содержащим сообщение об ошибке в поле 'name'
#     """
#     def __init__(self):
#         if config.UI_MODE.lower() == "web":
#             self.lock = RLock()
#         SimpleLogger().log("[Rutracker] : start init")
#         self.__rutracker = _retries_retry_operation(_Rutracker,
#                                                     username=config.RUTRACKER_LOGIN,
#                                                     password=config.RUTRACKER_PASS,
#                                                     proxy=config.proxy)
#
#         if not self.__rutracker:
#             SimpleLogger().log("[Rutracker] : error init")
#         else:
#             SimpleLogger().log("[Rutracker] : end init")
#
#
#     def get_tracker_list(self, search_request: str) -> list[ABCTorrentInfo]:
#         if config.UI_MODE.lower() == "web":
#             with self.lock:
#                 if self.__rutracker:
#                     list_ = _retries_retry_operation(self.__rutracker.get_search_list, search_request, 1)
#                     if list_:
#                         return list_
#                     else:
#                         return [TorrentInfo(name="Ошибка поиска. Попробуйте снова")]
#                 else:
#                     self.__init__()
#                     return [TorrentInfo(name="Ошибка подключений к рутрекеру. Попробуйте ввести запрос заново")]
#         else:
#             if self.__rutracker:
#                 list_ = _retries_retry_operation(self.__rutracker.get_search_list, search_request, 1)
#                 if list_:
#                     return list_
#                 else:
#                     return [TorrentInfo(name="Ошибка поиска. Попробуйте снова")]
#             else:
#                 self.__init__()
#                 return [TorrentInfo(name="Ошибка подключений к рутрекеру. Попробуйте ввести запрос заново")]



class Rutor(ABCTorrenTracker):
    '''
    Класс для взаимодействия с API Rutracker и выполнения поиска торрентов.

    Атрибуты:
    ----------
    connected : bool
        Флаг, указывающий, успешно ли выполнено подключение к Rutracker.

    Методы:
    -------
    __init__(username: str, password: str, proxy: str):
        Выполняет авторизацию на Rutracker с использованием предоставленных учетных данных и прокси.

    get_search_list(search_request: str, page_deepth: int = 2) -> list[TorrentInfo]:
        Выполняет поиск торрентов на Rutracker по заданному запросу. Возвращает список объектов `TorrentInfo`.
    '''


    def __init__(self, proxy: str | None = None):
        self.session = requests.Session()
        if proxy:
            self.session.proxies.update({
                "http": proxy,
                "https": proxy,
            })
        self._login()

    def _login(self,):
        payload = {
            "username": config.RUTOR_LOGIN,
            "password": config.RUTOR_PASS,
        }
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ru,en;q=0.9",
            "Connection": "keep-alive",
            # "Referer": f"{config.RUTOR_BASE_URL}/login/do"
        }
        r = self.session.post(
            f"{config.RUTOR_BASE_URL}/login/do",
            data=payload,
            headers=headers,
            allow_redirects=True
        )

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ru,en;q=0.9",
            "Connection": "keep-alive",
        })

        self.session.get("https://rutor.org")
        if not self._is_session_valid():
            raise RuntimeError("Session init failed")

    def _is_session_valid(self) -> bool:
        return "PHPSESSID" in self.session.cookies.get_dict()

    def get_tracker_list(self, search_request: str, page_deepth: int = 1) -> list[ABCTorrentInfo]:
        page = 1
        url = (
            f"{config.RUTOR_BASE_URL}/search/"
            f"{page}/0/000/0/{quote(search_request)}"
        )
        r = self.session.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        torrents = []
        rows = soup.select("tr.gai, tr.tum")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue
            date = cols[0].get_text(strip=True)
            links_cell = cols[1]
            title_tag = links_cell.select_one("a[href^='/torrent/']")
            download_tag = links_cell.select_one("a.downgif")
            magnet_tag = links_cell.select_one("a[href*='magnet']")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            torrent_url = (
                    config.RUTOR_BASE_URL + title_tag["href"]
            )
            download_url = (
                download_tag["href"]
                if download_tag else ""
            )
            magnet_url = (
                magnet_tag["href"]
                if magnet_tag else ""
            )
            size_mb = cols[2].get_text(strip=True)
            stats = cols[3].get_text(" ", strip=True)
            seeds = 0
            leeches = 0
            m = re.search(r"(\d+).*?(\d+)", stats)
            if m:
                seeds = int(m.group(1))
                leeches = int(m.group(2))
            torrents.append(
                TorrentInfo(
                    session=self.session,
                    name=title,
                    url=torrent_url,
                    # download_url=download_url,
                    # magnet_url=magnet_url,
                    size=size_mb,
                    seeds=seeds,
                    leeches=leeches,
                    year=date,
                )
            )
        return torrents




class _Rutracker:
    '''
    Класс для взаимодействия с API Rutracker и выполнения поиска торрентов.

    Атрибуты:
    ----------
    connected : bool
        Флаг, указывающий, успешно ли выполнено подключение к Rutracker.

    Методы:
    -------
    __init__(username: str, password: str, proxy: str):
        Выполняет авторизацию на Rutracker с использованием предоставленных учетных данных и прокси.

    get_search_list(search_request: str, page_deepth: int = 2) -> list[TorrentInfo]:
        Выполняет поиск торрентов на Rutracker по заданному запросу. Возвращает список объектов `TorrentInfo`.
    '''
    def __init__(self, username: str, password: str, proxy: str):
        """
        Инициализирует объект _Rutracker, выполняя авторизацию на Rutracker.
        """
        self.__rutracker = RutrackerApi(proxy=proxy)
        self.__rutracker.login(username, password)

    def get_search_list(self, search_request: str, page_deepth: int = 1) -> list[ABCTorrentInfo]:
        page = 1
        search = self.__rutracker.search(search_request, "desc", "seeds", page)
        search_results = search['result']
        if search['total_pages'] > search['page'] and search['page'] != page_deepth:
            page += 1
            search = self.__rutracker.search(search_request, "desc", "seeds", page)
            search_results += search['result']
        torrent_list = [TorrentInfo(name=res["title"],
                                    category=res["category"],
                                    url=res["url"],
                                    size=round(res["size"]/1048576, 2)) for res in search_results]
        print(f"get_search_list : {torrent_list}")
        return torrent_list





class RutorParserPage:
    """
    Простой парсер страницы раздачи Rutor.

    Особенности:
    - принимает готовый requests.Session
    - загружает страницу через session.get(...)
    - парсит основные данные из HTML страницы раздачи
    """

    def __init__(self, url: str, session: requests.Session, timeout: tuple[int, int] = (5, 10)):
        self.url = url
        self.session = session
        self.timeout = timeout
        self.__soup: Optional[BeautifulSoup] = None

    def __load_page(self) -> None:
        """
        Ленивая загрузка страницы.
        """
        if self.__soup is None and self.url:
            self.__soup = self.__loader(self.url)

    def __loader(self, url: str) -> BeautifulSoup:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def get_magnet_link(self) -> str:
        """
        Возвращает magnet-ссылку.
        В HTML она обычно в виде /magnet/<id>
        """
        self.__load_page()
        if not self.__soup:
            return ""

        magnet_link_tag = self.__soup.find("a", href=lambda href: href and "/magnet/" in href)
        if not magnet_link_tag:
            return ""

        href = magnet_link_tag.get("href", "").strip()
        if not href:
            return ""

        if href.startswith("http://") or href.startswith("https://") or href.startswith("magnet:"):
            return href

        return f"https://rutor.org{href}"

    def get_size(self) -> str:
        """
        Размер из строки:
        <td class="header">Размер</td><td>4.01 GB</td>
        """
        self.__load_page()
        if not self.__soup:
            return "Не удалось загрузить контент с Rutor"

        header_td = self.__soup.find("td", class_="header", string=lambda s: s and s.strip() == "Размер")
        if not header_td:
            return "Не удалось определить размер"

        value_td = header_td.find_next_sibling("td")
        if not value_td:
            return "Не удалось определить размер"

        return value_td.get_text(" ", strip=True)

    def get_other_data(self) -> List[List[str]]:
        """
        Собирает основные поля из основного блока описания:
        Страна, Год выпуска, Жанр, Тип, Продолжительность, Режиссер, Описание, и т.д.

        Возвращает список вида:
        [
            ["Страна", "Япония"],
            ["Год выпуска", "2014 г."],
            ...
        ]
        """
        self.__load_page()
        if not self.__soup:
            return [["", "Ошибка: Не удалось загрузить контент с Rutor"]]

        details_table = self.__soup.find("table", id="details")
        if not details_table:
            return [["", "Ошибка: Не удалось найти таблицу details"]]

        # Берём первую "полезную" ячейку с контентом
        content_td = details_table.find("td")
        if content_td:
            content_td = content_td.find_next_sibling("td")

        if not content_td:
            return [["", "Ошибка: Не удалось найти блок описания"]]

        data: List[List[str]] = []
        children = list(content_td.children)
        i = 0

        while i < len(children):
            node = children[i]

            if isinstance(node, Tag) and node.name == "b":
                key = node.get_text(" ", strip=True).rstrip(":").strip()
                if not key:
                    i += 1
                    continue

                value_parts: List[str] = []
                i += 1

                while i < len(children):
                    next_node = children[i]

                    # Следующее поле
                    if isinstance(next_node, Tag) and next_node.name == "b":
                        break

                    # Для некоторых полей значение идёт с <br>, но если уже что-то собрали —
                    # можно остановиться на двойном переносе логически.
                    if isinstance(next_node, Tag) and next_node.name == "div":
                        # hidewrap = техданные / эпизоды / скриншоты и т.д.
                        if "hidewrap" in (next_node.get("class") or []):
                            break

                    text = ""
                    if isinstance(next_node, Tag):
                        if next_node.name == "br":
                            # просто пропускаем br
                            i += 1
                            continue
                        text = next_node.get_text(" ", strip=True)
                    else:
                        text = str(next_node).strip()

                    if text:
                        value_parts.append(text)

                    i += 1

                value = " ".join(value_parts).strip()
                value = " ".join(value.split())

                if value:
                    data.append([key, value])
                else:
                    data.append([key, ""])
                continue
            i += 1
        return data if data else [["", "Ошибка: Не удалось извлечь данные"]]


if __name__ == '__main__':
    p = Rutor()
    a = p.get_tracker_list("anime")
    print()
    print(p[0].get_magnet, p[0].size, p[0].get_other_data)


