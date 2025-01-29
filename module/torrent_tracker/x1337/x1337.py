import requests
from bs4 import BeautifulSoup
import time
from module.torrent_tracker.TorrentInfoBase import AbstractTorrentInfo
import module.crypto_token.config as config


def _retries_retry_operation(func, *args, retries: int = 5, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Попытка {attempt + 1} из {retries}. Ошибка сети: ПОДКЛЮЧЕНИЯ 1337 {e}.")
            time.sleep(1)
    print(f"Не удалось загрузить 1337 после {retries} попыток.")
    return None


class TorrentInfo(AbstractTorrentInfo):
    """
    Класс объекта торрента содержащего все данные о торренте

    имеет несколько @property, берущих данные со страници
    """
    def __init__(self, url: str = None,
                 category: str = None,
                 name: str = None,
                 year: str = None,
                 magnet: str = None,
                 size: str = None,
                 seeds: str = None,
                 leeches: str = None):
        self.__category = category
        self.__name = name
        self.__year = year
        self.__url = url
        self.__parser = _1337ParserPage(self.__url)
        self.__size = size
        self.__seeds = seeds
        self.__leeches = leeches
        self.__id_torrent = None
    __slots__ = ('__category', '__name', '__year', '__url', '__parser', '__id_torrent', '__size', '__seeds', '__leeches')

    @property
    def name(self) -> str:
        return f"{self.__name[:110]}\n"

    @property
    def get_magnet(self) -> str:
        return self.__parser.get_magnet()

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
    def full_info(self) -> str:
        return (f"{self.__name}\n\n*Вес:* {self.__size}\n*Категория:* {self.__category}\n"
                f"*leeches:* {self.__leeches}\n*seeds:* {self.__seeds}\n*дата:* {self.__year}\n{self.get_other_data}\n"
                f"[страница]({self.__url})")

def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


@singleton
class X1337:
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
        self.base_url = 'https://1337x.to'
        self.__search_url = self.base_url + '/search/{}/1/'

        self.__proxies = {'http': proxy_ or config.proxy,
                          'https': proxy_ or config.proxy}



    def __get_search_list(self, query: str, search_url: str) -> [AbstractTorrentInfo]:
        search_url = search_url.format(query)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(search_url, headers=headers, proxies=self.__proxies)
        if response.status_code != 200:
            print(f"Error fetching the page: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='table-list')
        if not table:
            print("No torrents found.")
            return []

        torrent_list = []
        for row in table.find('tbody').find_all('tr'):
            name = row.find('td', class_='coll-1 name').find_all('a')[-1].text.strip()
            seeds = row.find('td', class_='coll-2 seeds').text.strip()
            leeches = row.find('td', class_='coll-3 leeches').text.strip()
            upload_date = row.find('td', class_='coll-date').text.strip()
            url = row.find('td', class_='coll-1 name').find_all('a')[-1]['href']
            size_cell = row.find('td', class_="coll-4 size mob-uploader")
            if not size_cell:
                size_cell = row.find('td', class_="coll-4 size mob-user")
            size = "None"
            if size_cell:
                size = size_cell.contents[0].strip()

            torrent_list.append(TorrentInfo(url=self.base_url + url,
                                            name=name,
                                            seeds=seeds,
                                            leeches=leeches,
                                            year=upload_date,
                                            size=size,
                                            ))
        return torrent_list

    def get_tracker_list(self, search_request: str) -> list[AbstractTorrentInfo]:
        list_ = _retries_retry_operation(self.__get_search_list, search_request, self.__search_url)
        if list_:
            return list_
        else:
            return [TorrentInfo(name="Ошибка поиска. Попробуйте снова")]



class _1337ParserPage:
    """
    Простой парсер страниц
    """
    def __init__(self, url: str):
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


    def get_magnet(self):
        self.__load_page()
        if self.__soup:
            link = self.__soup.find('a', id='openPopup', href=True)
            if link and link['href'].startswith('magnet:'):
                return link['href']
            return None

    def get_other_data(self) -> str:
        return "other_data = None"


if __name__ == '__main__':
    p = X1337().get_tracker_list("python")
    print(p[0].get_magnet)
