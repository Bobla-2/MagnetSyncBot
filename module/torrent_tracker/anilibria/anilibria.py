import requests
from bs4 import BeautifulSoup
import time
from module.torrent_tracker.TorrentInfoBase import ABCTorrentInfo, ABCTorrenTracker
import module.crypto_token.config as config


def _retries_retry_operation(func, *args, retries: int = 5, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Попытка {attempt + 1} из {retries}. Ошибка сети: ПОДКЛЮЧЕНИЯ Anilibria {e}.")
            time.sleep(1)
    print(f"Не удалось загрузить 1337 после {retries} попыток.")
    return None


class TorrentInfo(ABCTorrentInfo):
    """
    Класс объекта торрента содержащего все данные о торренте

    имеет несколько @property, берущих данные со страници
    """
    __slots__ = ('__category', '__name', '__year', '__url', '__parser', '__id_torrent', '__size', '__seeds', '__leeches',
                 '__short_categories', '__id', '__magnet', '__data')

    def __init__(self, url: str = None,
                 id: int = None,
                 category: str = '',
                 name: str = None,
                 year: str = None,
                 magnet: str = None,
                 size: str = None,
                 data = None,
                 seeds: str = None,
                 leeches: str = None):
        self.__category = category
        self.__magnet = magnet
        self.__data = data
        self.__id = id
        self.__name = name
        self.__year = year
        self.__url = url
        self.__size = int(size) / 1_048_576
        self.__size = f'{round(self.__size, 2)} MB' if self.__size < 800. else f'{round(self.__size / 1024, 2)} GB'
        self.__seeds = seeds
        self.__leeches = leeches
        self.__id_torrent = None
        self.__short_categories = ''

    @property
    def name(self) -> str:
        return f"{self.escape_special_chars_translate(self.__name[:101])}"

    @property
    def size(self) -> str:
        return self.__size

    @property
    def get_magnet(self) -> str:
        return self.__magnet

    @property
    def get_other_data(self) -> str:
        data_str = []
        current_length = 0
        for dt in self.__data:
            string = f"*{self.escape_special_chars_translate(dt[0])}:* {self.escape_special_chars_translate(dt[1])}"
            data_str.append(string)
            current_length += len(string)
            if current_length > 1950:
                break
        return "\n".join(data_str)

    @property
    def id_torrent(self) -> str:
        return self.__id_torrent

    @id_torrent.setter
    def id_torrent(self, id_: str | int):
        self.__id_torrent = id_

    @property
    def category(self) -> str:
        return ""

    def escape_special_chars_translate(self, text: str) -> str:
        special_chars = '_*[~`#=|{}\\'
        translation_table = str.maketrans({char: f'\\{char}' for char in special_chars})
        return text.translate(translation_table)

    @property
    def full_info(self) -> str:
        return (f"{self.escape_special_chars_translate(self.__name)}\n\n"
                f"*leeches:* {self.__leeches}\n*seeds:* {self.__seeds}\n*дата:* {self.__year}\n{self.get_other_data}\n"
                f"[страница]({self.__url})")

    @property
    def short_category(self) -> str | None:
        if not self.__short_categories:
            for categories, _, condition, short_categories in config.MEDIA_EXTENSIONS:
                if condition == "==":
                    if self.__category in categories:
                        self.__short_categories = short_categories
                elif condition == "in":
                    if any(cat in self.__category for cat in categories):
                        self.__short_categories = short_categories

            if not self.__short_categories:
                self.__short_categories = "other"
        return self.__short_categories


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


@singleton
class Anilibria(ABCTorrenTracker):
    '''
    Класс для взаимодействия с  1337 и выполнения поиска торрентов.

    Методы:
    -------
    __init__():
        Выполняет авторизацию на 1337

    get_search_list(search_request: str, page_deepth: int = 2) -> list[TorrentInfo]:
        Выполняет поиск торрентов на 1337 по заданному запросу. Возвращает список объектов `TorrentInfo`.
    '''

    def __init__(self, proxy_=None):
        self.base_url = config.ANILIBRIA_BASE_URL
        self.__search_url = self.base_url + '/api/v1/app/search/releases?query={}'
        self.__torrent_url = self.base_url + '/api/v1/anime/torrents/release/{}'

        self.__proxies = {'http': proxy_ or config.proxy,
                          'https': proxy_ or config.proxy}

    def __get_search_list(self, query: str, search_url: str, torrent_url: str) -> list[ABCTorrentInfo]:
        search_url = search_url.format(query)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        response = requests.get(search_url, headers=headers, proxies=self.__proxies)
        if response.status_code != 200:
            print(f"Error fetching the page: {response.status_code}")
            return []
        else:
            data = response.json()
            torrent_list = []
            url_part_one = '/anime/releases/release/'
            url_part_two = '/episodes'
            for dt in data:
                id = dt["id"]
                torrent_url_s = torrent_url.format(id)
                response = requests.get(torrent_url_s, headers=headers, proxies=self.__proxies)
                if response.status_code == 200:
                    torrent_info = response.json()
                else:
                    torrent_info = {"magnet": None}

                for tr_inf in torrent_info:

                    all_data = [["Вид", tr_inf["type"]["value"]],
                                ["Кодек", tr_inf["codec"]["value"]],
                                ["Качество", tr_inf["quality"]["description"]],
                                ["имя", dt["name"]["english"]],
                                # ["имя англ.", tr_inf["name"]["english"]]
                                ]

                    torrent_list.append(TorrentInfo(url=self.base_url + url_part_one + dt["alias"] + url_part_two,
                                                    name=dt["name"]["main"],
                                                    id=id,
                                                    year=dt["year"],
                                                    category="anime",
                                                    magnet=tr_inf["magnet"],
                                                    seeds=tr_inf["seeders"],
                                                    leeches=tr_inf["leechers"],
                                                    size=tr_inf["size"],
                                                    data=all_data
                                                    ))

        return torrent_list

    def get_tracker_list(self, search_request: str) -> list[ABCTorrentInfo]:
        list_ = _retries_retry_operation(self.__get_search_list, search_request,
                                         self.__search_url, self.__torrent_url)
        if list_:
            return list_
        else:
            return [TorrentInfo(name="Ошибка поиска. Попробуйте снова")]


if __name__ == '__main__':
    p = Anilibria().get_tracker_list("Kanojo, Okarishimasu 4th Season")
    print(p[0].get_magnet, p[0].size)
