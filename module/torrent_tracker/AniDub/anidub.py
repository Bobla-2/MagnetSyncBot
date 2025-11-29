import requests
from bs4 import BeautifulSoup
import time
from module.torrent_tracker.TorrentInfoBase import ABCTorrentInfo, ABCTorrenTracker
import module.crypto_token.config as config
import bencodepy
import hashlib
import urllib.parse


def _retries_retry_operation(func, *args, retries: int = 5, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Попытка {attempt + 1} из {retries}. Ошибка сети: ПОДКЛЮЧЕНИЯ anidub {e}.")
            time.sleep(1)
    print(f"Не удалось загрузить anidub после {retries} попыток.")
    return None



class TorrentInfo(ABCTorrentInfo):
    """
    Класс объекта торрента содержащего все данные о торренте
    имеет несколько @property, берущих данные со страници
    """
    __slots__ = ('__category', '__name', '__year', '__url', '__parser', '__id_torrent', '__size', '__seeds', '__leeches',
                 '__short_categories')

    def __init__(self, url: str = None,
                 category: str = '',
                 name: str = None):
        self.__category = category
        self.__name = name
        self.__url = url
        self.__parser = _AniDubParserPage(self.__url)
        self.__id_torrent = None
        self.__short_categories = ''

    @property
    def name(self) -> str:
        return f"{TorrentInfo.escape_special_chars_translate(self.__name[:101])}"

    @property
    def size(self) -> str:
        return self.__parser.get_size()

    @property
    def get_magnet(self) -> str:
        return self.__parser.get_magnet()

    @property
    def get_other_data(self) -> str:
        data = self.__parser.get_other_data()
        data_str = []
        current_length = 0
        for dt in data:
            string = f"*{TorrentInfo.escape_special_chars_translate(dt[0])}:* {TorrentInfo.escape_special_chars_translate(dt[1])}"
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
        return self.__category

    @property
    def full_info(self) -> str:
        return (f"{TorrentInfo.escape_special_chars_translate(self.__name)}\n\n"
                f"*seeds:* {self.__parser.get_seeders()}\n{self.get_other_data}\n"
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

    @staticmethod
    def escape_special_chars_translate(text: str) -> str:
        special_chars = '_*[~`#=|{}\\'
        translation_table = str.maketrans({char: f'\\{char}' for char in special_chars})
        return text.translate(translation_table)


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


@singleton
class AniDub(ABCTorrenTracker):
    """
    Класс для взаимодействия с  AniDub и выполнения поиска торрентов.

    Методы:
    -------
    __init__():
        Выполняет авторизацию на AniDub

    get_search_list(search_request: str, page_deepth: int = 2) -> list[TorrentInfo]:
        Выполняет поиск торрентов на AniDub по заданному запросу. Возвращает список объектов `TorrentInfo`.
    """

    def __init__(self, proxy_=None):
        self.base_url = config.ANIDUB_BASE_URL
        self.__search_url = self.base_url

        self.__proxies = {'http': proxy_ or config.proxy,
                          'https': proxy_ or config.proxy}

    def __get_search_list(self, query: str, search_url: str) -> list[ABCTorrentInfo]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        data = {
            "do": "search",
            "subaction": "search",
            "story": query
        }

        response = requests.post(search_url, headers=headers, data=data, proxies=self.__proxies)
        if response.status_code != 200:
            print(f"Error fetching the page: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find(class_='search_post')
        if not table:
            print("No torrents found.")
            return [TorrentInfo(category="anime",
                                name="Найдено 0 аниме",
                                )]
        results = []
        for block in soup.select("div.search_post"):
            a_tag = block.select_one("h2 > a")
            if a_tag:
                title = a_tag.text.strip()
                link = a_tag["href"]
                results.append((title, link))

        # Печатаем результат
        torrent_list = []
        for title, link in results:
            print(f"{title}\n{link}\n")

            torrent_list.append(TorrentInfo(category="anime",
                                        name=title,
                                        url=link,
                                        ))
        return torrent_list

    def get_tracker_list(self, search_request: str) -> list[ABCTorrentInfo]:
        list_ = _retries_retry_operation(self.__get_search_list, search_request, self.__search_url)
        if list_:
            return list_
        else:
            return [TorrentInfo(name="Ошибка поиска. Попробуйте снова")]


class _AniDubParserPage:
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

    @staticmethod
    def __loader(url: str, proxies):
        response = requests.get(url, proxies=proxies)
        response.raise_for_status()
        page_content = response.text
        return BeautifulSoup(page_content, "html.parser")

    def get_magnet(self):
        self.__load_page()
        relative_url = ''
        if self.__soup:
            for a in self.__soup.find_all('a', href=True):
                if "download.php?id=" in a['href']:
                    relative_url = a['href']
                    break
            if not relative_url:
                return ''

            full_url = urllib.parse.urljoin(config.ANIDUB_BASE_URL, relative_url)
            # Шаг 2: Скачать файл
            response = requests.get(full_url)
            response.raise_for_status()

            # Шаг 3: Распарсить .torrent
            torrent_data = bencodepy.decode(response.content)
            info = torrent_data[b'info']
            info_bencoded = bencodepy.encode(info)
            info_hash = hashlib.sha1(info_bencoded).hexdigest()

            # Шаг 4: Извлечь имя и трекеры
            name = info.get(b'name', b'torrent').decode('utf-8')
            trackers = []

            if b'announce' in torrent_data:
                trackers.append(torrent_data[b'announce'].decode())

            if b'announce-list' in torrent_data:
                for tier in torrent_data[b'announce-list']:
                    for url in tier:
                        url_str = url.decode()
                        if url_str not in trackers:
                            trackers.append(url_str)

            # Шаг 5: Собрать magnet-ссылку
            params = {
                'xt': f'urn:btih:{info_hash}',
                'dn': name
            }

            magnet = f"magnet:?{urllib.parse.urlencode(params)}"
            for tr in trackers:
                magnet += f"&tr={urllib.parse.quote(tr)}"
        else:
            raise ValueError("не найдена магнет ссылка в анидаб. if download.php?id= in a['href']:")
        return magnet

    def get_seeders(self):
        self.__load_page()
        if not self.__soup:
            return "Не удалось загрузить контент с AniDub"
        block = self.__soup.find('div', class_='list down')
        seeders = block.find('span', class_='li_distribute_m').text.strip()
        return seeders

    def get_size(self):
        self.__load_page()
        if not self.__soup:
            return "Не удалось загрузить контент с AniDub"
        block = self.__soup.find('div', class_='list down')
        size = block.find('span', class_='red').text.strip()
        return size

    def get_year(self) -> str:
        self.__load_page()
        if not self.__soup:
            return "Не удалось загрузить контент с AniDub"
        block = self.__soup.find('div', class_='xfinfodata')
        if block:
            year_label = block.find('b', string=lambda t: t and "Год" in t)
            if year_label:
                year_span = year_label.find_next_sibling("span")
                if year_span:
                    year = year_span.get_text(strip=True)
                    return year or "Год не найден"
        return "Год не найден"

    def get_other_data(self) -> list[list[str]]:
        self.__load_page()
        if not self.__soup:
            return [["Ошибка", "Не удалось загрузить контент с AniDub"]]

        block = self.__soup.find('div', class_='xfinfodata')
        if not block:
            return [["Ошибка", "Блок с информацией не найден"]]

        result = []
        for b in block.find_all("b"):
            title = b.get_text(strip=True).rstrip(":")  # например "Год", "Жанр"
            span = b.find_next_sibling("span")
            if not span:
                continue

            # собираем весь текст из span (учитываем <a>, запятые и т.д.)
            value = ", ".join(a.get_text(strip=True) for a in span.find_all("a")) or span.get_text(strip=True)
            result.append([title, value])

        return result


if __name__ == '__main__':
    p = AniDub().get_tracker_list("Перевоплотился в седьмого принца, так что я буду совершенствовать свою магию, как захочу ТВ-2")
    print(p[0].get_magnet)
