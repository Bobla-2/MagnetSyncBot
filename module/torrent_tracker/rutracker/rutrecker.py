import requests
from bs4 import BeautifulSoup
from module.torrent_tracker.rutracker.rutracker_api.main import RutrackerApi
import time
import module.crypto_token.config as config
from module.torrent_tracker.TorrentInfoBase import ABCTorrentInfo, ABCTorrenTracker
from module.logger.logger import SimpleLogger
import bencodepy
import hashlib
import urllib.parse
from module.other.singleton import singleton
from threading import Lock


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
    __slots__ = ('__category', '__name', '__year', '__url', '__size_', '__parser', '__id_torrent', '__forum_name', '__short_categories')

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
    def get_other_data(self) -> str:
        data = self.__parser.get_other_data()
        data = [["Вес" , self.__size_], ["Категория", self.__category]] + data
        return data


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

    def escape_special_chars_translate(self, text: str) -> str:
        special_chars = '_*[~`#=|{}\\'
        translation_table = str.maketrans({char: f'\\{char}' for char in special_chars})
        return text.translate(translation_table)

    # @property
    # def full_info(self) -> str:
    #     return (f"{self.escape_special_chars_translate(self.__name)}\n\n*Вес:* {self.__size_}\n*Категория:* {self.__category}\n{self.get_other_data}\n"
    #             f"[страница]({self.__url})")

    @property
    def url(self) -> str:
        return self.__url



@singleton
class Rutracker(ABCTorrenTracker):
    """
    Класс (абстракция на _Rutracker) для инициализации использует данные из crypto_token.config

    добавляет retry_operation при использовании всех функций
    в случае неудачи возвращает список с TorrentInfo содержащим сообщение об ошибке в поле 'name'
    """
    def __init__(self):
        if config.UI_MODE.lower() == "web":
            self.lock = Lock()
        SimpleLogger().log("[Rutracker] : start init")
        self.__rutracker = _retries_retry_operation(_Rutracker,
                                                    username=config.login_rutreker,
                                                    password=config.pass_rutreker,
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
        print(torrent_list)
        return torrent_list


class RutrackerParserPage:
    """
    Простой парсер страниц рутрекера
    """
    def __init__(self, url):
        self.url = url
        self.__soup = None

    def __load_page(self):
        """
        Внутренний метод, скачивающий html файл страници
        Нужно вызывать во всех функциях
        """
        if not self.__soup and self.url:
            proxies = {'http': config.proxy,
                       'https': config.proxy}
            self.__soup = _retries_retry_operation(self.__loader, url=self.url, proxies=proxies)

    def __loader(self, url: str, proxies):
        response = requests.get(url, proxies=proxies, timeout=(5, 10))
        response.raise_for_status()
        page_content = response.text
        return BeautifulSoup(page_content, "html.parser")

    def get_magnet_link(self) -> str:
        self.__load_page()
        if self.__soup:
            magnet_link_tag = self.__soup.find('a', href=lambda href: href and href.startswith('magnet:'))
            if magnet_link_tag:
                return magnet_link_tag['href']
        return ""


    def get_size(self) -> str:
        self.__load_page()
        if self.__soup:
            size_element = self.__soup.find("li", text=lambda t: t and ("GB" in t or "MB" in t))
            if size_element:
                size_text = size_element.get_text(strip=True)
                return size_text
        return "Не удалось загрузить контент с Rutracker"

    def get_other_data(self) -> list:
        self.__load_page()
        if self.__soup:
            post_body = self.__soup.find("div", class_="post_body")

            if not post_body:
                return [['', "Ошибка: Не удалось загрузить контент с  Rutracker"]]
            data = []
            # print(post_body.find_all("span", class_="post-b"))
            for element in post_body.find_all("span", class_="post-b"):
                key = element.get_text(strip=True).rstrip(":")  # Название поля
                sibling = element.next_sibling
                while sibling and not isinstance(sibling, str):
                    sibling = sibling.next_sibling

                value = sibling.strip() if sibling else ""  # Значение
                data.append([key, value])
            return data
        return [['', "Ошибка: Не удалось загрузить контент с  Rutracker"]]


if __name__ == '__main__':
    p = Rutracker().get_tracker_list("PyCharm")
    print(p[0].get_magnet, p[0].size)


