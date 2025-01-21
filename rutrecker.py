import requests
from bs4 import BeautifulSoup
from rutracker_api.main import RutrackerApi
import re
import time
from module.crypto_token.config import get_pass_rutreker, get_login_rutreker, proxy
from datetime import datetime

class TorrentInfo:
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
    def full_info(self) -> str:
        return f"{self.name}\n\nВес: {self.size}\nКатегория: {self.category}"


def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class Rutracker:
    def __init__(self):
        self.__rutracker = _RutrackerSerch(
            username=get_login_rutreker(),
            password=get_pass_rutreker(),
            proxy=proxy
        )
    def get_anime_list(self, search_request: str) -> list[TorrentInfo]:
        torrents_search = self.__rutracker.get_search_list(search_request, 1)
        return torrents_search



class _RutrackerSerch:
    def __init__(self, username, password, proxy):
        retries = 3  # Количество попыток
        for attempt in range(retries):
            try:
                self.rutracker = RutrackerApi(proxy=proxy)
                self.rutracker.login(username, password)
                return
            except Exception as e:
                print(f"Попытка {attempt + 1} из {retries}. Ошибка сети: ПОДКЛЮЧЕНИЯ Rutracker {e}.")
                time.sleep(1)
        print(f"Не удалось загрузить страницу после {retries} попыток.")

    def get_search_list(self, search_request, page_deepth=2) -> list[TorrentInfo]:
        # anime_categories = ['Аниме (DVD Video)', 'Аниме (SD Video)', 'Аниме (HD Video)']
        page = 1
        search = self.rutracker.search(search_request, "desc", "size", page)
        search_results = search['result']
        if search['total_pages'] > search['page'] and search['page'] != page_deepth:
            page += 1
            search = self.rutracker.search(search_request, "desc", "size", page)
            search_results += search['result']
        torrent_list = [TorrentInfo(name=res["title"],
                                    category=res["category"],
                                    url=res["url"]) for res in search_results]
        print(torrent_list)
        return torrent_list

    # def get_magnet(self, url: str, torent: TorrentInfo) -> None:
    #     pass


class RutrackerParserPage:
    def __init__(self, url):
        self.url = url
        self.page = False
    def load_page(self):
        if not self.page:
            proxies = {
                'http': proxy,
                'https': proxy,
            }
            retries = 3  # Количество попыток
            for attempt in range(retries):
                try:
                    response = requests.get(self.url, proxies=proxies)
                    response.raise_for_status()  # Проверка статуса ответа
                    self.page_content = response.text
                    self.soup = BeautifulSoup(self.page_content, "html.parser")
                    self.page = True
                    return
                except Exception as e:
                    print(f"Попытка {attempt + 1} из {retries}. Ошибка сети: Rutracker {e}.")
                    time.sleep(1)

            print(f"Не удалось загрузить страницу после {retries} попыток.")
            return

    def get_magnet_link(self):
        self.load_page()
        if self.page:
            magnet_link_tag = self.soup.find('a', href=lambda href: href and href.startswith('magnet:'))
            if magnet_link_tag:
                return magnet_link_tag['href']
        return None

    def get_size(self):
        self.load_page()
        if self.page:
            size_element = self.soup.find("li", text=lambda t: t and ("GB" in t or "MB" in t))
            if size_element:
                size_text = size_element.get_text(strip=True)
                return size_text
        return "Ошибка размера"


