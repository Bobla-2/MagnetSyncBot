import requests
from bs4 import BeautifulSoup
from module.torrent_tracker.rutracker.rutracker_api.main import RutrackerApi
import time
from module.crypto_token.config import get_pass_rutreker, get_login_rutreker, proxy
import module.crypto_token.config as config
from module.torrent_tracker.TorrentInfoBase import ABCTorrentInfo

def _retries_retry_operation(func, *args, retries: int = 5, **kwargs):
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
    __slots__ = ('__category', '__name', '__year', '__url', '__parser', '__id_torrent', '__forum_name')

    def __init__(self, category: str = '',
                 name: str = None,
                 year: str = None,
                 url: str = None,
                 forum_name: str = None):
        self.__forum_name = forum_name
        self.__category = category
        self.__name = name
        self.__year = year
        self.__url = url
        # self.magnet = magnet
        self.__parser = RutrackerParserPage(self.__url)
        self.__id_torrent = None

    @property
    def name(self) -> str:
        return f"{self.__name[:110]}\n"

    @property
    def __size(self) -> str:
        return self.__parser.get_size()

    @property
    def get_magnet(self) -> str:
        return self.__parser.get_magnet_link()

    @property
    def get_other_data(self) -> str:
        return self.__parser.get_other_data()

    @property
    def id_torrent(self) -> str:
        return self.__id_torrent

    @id_torrent.setter
    def id_torrent(self, id_: str | int):
        self.__id_torrent = id_

    @property
    def short_category(self) -> str | None:
        for categories, _, condition, short_categories in config.MEDIA_EXTENSIONS:
            if condition == "==":
                if self.__category in categories:
                    return short_categories
            elif condition == "in":
                if any(cat in self.__category for cat in categories):
                    return short_categories
        return None

    @property
    def full_info(self) -> str:
        return (f"{self.__name}\n\n*Вес:* {self.__size}\n*Категория:* {self.__category}\n{self.get_other_data[:2000]}\n"
                f"[страница]({self.__url})")


def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class Rutracker:
    """
    Класс (абстракция на _Rutracker) для инициализации использует данные из crypto_token.config

    добавляет retry_operation при использовании всех функций
    в случае неудачи возвращает список с TorrentInfo содержащим сообщение об ошибке в поле 'name'
    """
    def __init__(self):

        self.__rutracker = _retries_retry_operation(_Rutracker,
                                                    username=get_login_rutreker(),
                                                    password=get_pass_rutreker(),
                                                    proxy=config.proxy)

    def get_tracker_list(self, search_request: str) -> list[ABCTorrentInfo]:
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
    def __init__(self, username, password, proxy):
        """
        Инициализирует объект _Rutracker, выполняя авторизацию на Rutracker.
        """
        self.__rutracker = RutrackerApi(proxy=proxy)
        self.__rutracker.login(username, password)

    def get_search_list(self, search_request, page_deepth=1) -> list[ABCTorrentInfo]:
        page = 1
        search = self.__rutracker.search(search_request, "desc", "size", page)
        search_results = search['result']
        if search['total_pages'] > search['page'] and search['page'] != page_deepth:
            page += 1
            search = self.__rutracker.search(search_request, "desc", "size", page)
            search_results += search['result']
        torrent_list = [TorrentInfo(name=res["title"],
                                    category=res["category"],
                                    url=res["url"]) for res in search_results]
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
        response = requests.get(url, proxies=proxies)
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
        return "Ошибка размера"


    def get_other_data(self) -> str:
        self.__load_page()
        if self.__soup:
            post_body = self.__soup.find("div", class_="post_body")

            if not post_body:
                return "Ошибка: Данные не найдены"
            data = []
            # print(post_body.find_all("span", class_="post-b"))
            for element in post_body.find_all("span", class_="post-b"):
                key = element.get_text(strip=True).rstrip(":")  # Название поля
                sibling = element.next_sibling
                while sibling and not isinstance(sibling, str):
                    sibling = sibling.next_sibling

                value = sibling.strip() if sibling else ""  # Значение
                data.append(f"*{key}* {value}")
            return "\n".join(data)


if __name__ == '__main__':
    p = Rutracker().get_tracker_list("python")
    print(p[0].get_magnet)


