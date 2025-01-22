import requests
from bs4 import BeautifulSoup
from module.rutracker.rutracker_api.main import RutrackerApi
import time
from module.crypto_token.config import get_pass_rutreker, get_login_rutreker, proxy

class TorrentInfo:
    """
    Класс объекта торрента содержащего все данные о торренте

    имеет несколько @property, берущих данные со страници рутрекера через парсер RutrackerParserPage
    """
    __slots__ = ('category', 'name', 'year', 'url', 'magnet', '__parser', 'id_torrent')
    def __init__(self, category: str = None,
                 name: str = None,
                 year: str = None,
                 magnet: str = None,
                 url: str = None):
        self.category = category
        self.name = name
        self.year = year
        self.url = url
        self.magnet = magnet
        self.__parser = RutrackerParserPage(self.url)
        self.id_torrent = None

    def __str__(self):
        return f"{self.name[:110]}\n"

    @property
    def size(self) -> str:
        return self.__parser.get_size()

    @property
    def get_magnet(self) -> str:
        return self.__parser.get_magnet_link()

    @property
    def get_other_data(self) -> str:
        return self.__parser.get_other_data()

    @property
    def full_info(self) -> str:
        return f"{self.name}\n\n*Вес:* {self.size}\n*Категория:* {self.category}\n{self.get_other_data}"


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

    добавляет проверку на корректность при использовании get_anime_list
    в случае неудачи возвращает список с TorrentInfo содержащим сообщение об ошибке
    """
    def __init__(self):
        self.__rutracker = _Rutracker(
            username=get_login_rutreker(),
            password=get_pass_rutreker(),
            proxy=proxy)

    def get_anime_list(self, search_request: str) -> list[TorrentInfo]:
        if self.__rutracker.connected:
            try:
                return self.__rutracker.get_search_list(search_request, 1)
            except Exception as e:
                return [TorrentInfo(name="Ошибка поиска. Попробуйте снова")]
        return [TorrentInfo(name="Ошибка подключений к рутрекеру. Попробуйте зарегистрироваться заново")]


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
        retries = 3  # Количество попыток
        self.connected = False
        for attempt in range(retries):
            try:
                self.__rutracker = RutrackerApi(proxy=proxy)
                self.__rutracker.login(username, password)
                self.connected = True
                return
            except Exception as e:
                print(f"Попытка {attempt + 1} из {retries}. Ошибка сети: ПОДКЛЮЧЕНИЯ Rutracker {e}.")
                time.sleep(1)
        print(f"Не удалось загрузить RutrackerApi после {retries} попыток.")



    def get_search_list(self, search_request, page_deepth=1) -> list[TorrentInfo]:
        # anime_categories = ['Аниме (DVD Video)', 'Аниме (SD Video)', 'Аниме (HD Video)']
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
        self.__page = False
        self.__soup = None

    def __load_page(self):
        """
        Внутренний метод, скачивающий html файл страници

        Нужно вызывать во всех функциях
        """
        if not self.__page:
            proxies = {
                'http': proxy,
                'https': proxy,
            }
            retries = 3  # Количество попыток
            for attempt in range(retries):
                try:
                    if self.url:
                        response = requests.get(self.url, proxies=proxies)
                        response.raise_for_status()
                        page_content = response.text
                        self.__soup = BeautifulSoup(page_content, "html.parser")
                        self.__page = True
                        return
                except Exception as e:
                    print(f"Попытка {attempt + 1} из {retries}. Ошибка сети: Rutracker {e}.")
                    time.sleep(1)

            print(f"Не удалось загрузить страницу после {retries} попыток.")
            return

    def get_magnet_link(self) -> str:
        self.__load_page()
        if self.__page:
            magnet_link_tag = self.__soup.find('a', href=lambda href: href and href.startswith('magnet:'))
            if magnet_link_tag:
                return magnet_link_tag['href']
        return ""

    def get_size(self) -> str:
        self.__load_page()
        if self.__page:
            size_element = self.__soup.find("li", text=lambda t: t and ("GB" in t or "MB" in t))
            if size_element:
                size_text = size_element.get_text(strip=True)
                return size_text
        return "Ошибка размера"


    def get_other_data(self) -> str:
        self.__load_page()
        if self.__page:
            post_body = self.__soup.find("div", class_="post_body")

            if not post_body:
                return "Ошибка: Данные не найдены"

            data = []

            # Проходим по всем элементам с классом post-b
            for element in post_body.find_all("span", class_="post-b"):
                key = element.get_text(strip=True).rstrip(":")  # Название поля
                value = element.next_sibling.strip() if element.next_sibling else ""  # Значение
                data.append(f"*{key}* {value}")

            return "\n".join(data)



