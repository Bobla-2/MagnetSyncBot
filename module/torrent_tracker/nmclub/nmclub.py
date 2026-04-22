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
from threading import Lock
import re
from urllib.parse import urlencode
import requests
from urllib.parse import quote_plus


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
            print(f"Попытка {attempt + 1} из {retries}. Ошибка сети: ПОДКЛЮЧЕНИЯ NNMClub {e}.")
            time.sleep(0.3)
    print(f"Не удалось загрузить NNMClub после {retries} попыток.")
    return None


class TorrentInfo(ABCTorrentInfo):
    """
    Класс объекта торрента содержащего все данные о торренте

    имеет несколько @property, берущих данные со страници рутрекера через парсер RutrackerParserPage
    """
    __slots__ = ('__seeds', '__leeches', '__category', '__name', '__year', '__url', '__size_', '__parser', '__id_torrent', '__short_categories', '__other_data')

    def __init__(self, category: str = '',
                 name: str = None,
                 year: str = "",
                 url: str = None,
                 seeds: str = None,
                 leeches: str = None,
                 magnet_link: str = None,
                 size: str = None):
        # print(f"magnet_link {magnet_link}")
        self.__category = category
        self.__name = name
        self.__year = year
        self.__url = f"{config.NMCLUB_BASE_URL}/forum/{url}"
        self.__seeds = seeds
        self.__leeches = leeches
        self.__parser = NmClubParserPage(self.__url)
        self.__id_torrent = None
        self.__short_categories = ''
        self.__other_data = None
        self.__size_ = size
        # self.__size_ = f'{size} MB' if size < 800. else f'{round(size / 1024, 2)} GB'

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
            data = [["Вес" , self.__size_], ["Категория", self.__category],
                    ["leeches", self.__leeches], ["seeds", self.__seeds]] + data
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

    def escape_special_chars_translate(self, text: str) -> str:
        special_chars = '_*[~`#=|{}\\'
        translation_table = str.maketrans({char: f'\\{char}' for char in special_chars})
        return text.translate(translation_table)

    @property
    def season(self) -> int:
        m = SEASON_RE.search(self.__name)
        return int(m.group(1) or m.group(2)) if m else 1

    @property
    def qualiti(self) -> str:
        title = f"{self.__name}"#{data_str}"

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

class NmClub(ABCTorrenTracker):
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
        self.base_url = config.NMCLUB_BASE_URL
        self.__search_url = self.base_url + "/forum/tracker.php"

        self.__proxies = {'http': proxy_ or config.proxy,
                          'https': proxy_ or config.proxy}

    def __get_search_list(self, query: str, search_url: str) -> list[ABCTorrentInfo]:
        # base_url = "https://nnmclub.to"
        # search_url = base_url + "/forum/tracker.php"
        # query = "Повелитель тайн"
        #
        # nm_enc = quote_plus(query.encode("cp1251"))
        # submit_enc = quote_plus("Искать".encode("cp1251"))
        #
        # body = f"f=-1&nm={nm_enc}&search_submit={submit_enc}"
        #
        # s = requests.Session()
        #
        # headers_get = {
        #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        #     "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        #     "Referer": search_url,
        # }
        #
        # r0 = s.get(search_url, headers=headers_get, timeout=20)
        # print("GET status:", r0.status_code)
        # print("cookies after GET:", s.cookies.get_dict())
        #
        # headers_post = {
        #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        #     "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        #     "Content-Type": "application/x-www-form-urlencoded",
        #     "Origin": base_url,
        #     "Referer": search_url,
        # }
        #
        # r = s.post(search_url, headers=headers_post, data=body, timeout=20)
        # r.encoding = "cp1251"

        #
        payload = {
            "f": "-1",
            "nm": query,
            "search_submit": "%C8%F1%EA%E0%F2%FC",
        }
        # data = payload
        data = urlencode(payload, encoding="cp1251").encode("ascii")

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://nnmclub.to/forum/tracker.php",
            "Origin": "https://nnmclub.to",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        r = requests.post(search_url, headers=headers, data=data, proxies=self.__proxies)
        if r.status_code != 200:
            print(f"Error fetching the page: {r.status_code}")
            SimpleLogger().log(f"[NNMClub] : Error fetching the page: {r.status_code}")
            return []

        # if 'value="Повелитель тайн"' in r.text and "Результатов поиска:" in r.text:
        #     print("поиск сработал")

        r.encoding = 'cp1251'
        soup = BeautifulSoup(r.text, 'html.parser')

        results_table = soup.find('table', class_='forumline tablesorter')
        if not results_table:
            SimpleLogger().log("[NNMClub] : No torrents table found.")
            return [TorrentInfo(
                category="torrent",
                name="Ошибка поиска. Попробуйте снова",
            )]

        rows = soup.select("tr.prow1, tr.prow2")
        if not rows:
            SimpleLogger().log("[NNMClub] : No torrents found.")
            return [TorrentInfo(
                category="",
                name="Ничего не найдено",
            )]

        torrent_list = []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 10:
                continue

            forum_tag = cols[1].find("a")
            topic_tag = cols[2].find("a", class_=["genmed", "topictitle", "topicpremod"])
            author_tag = cols[3].find("a")
            dl_tag = cols[4].find("a")
            status_img = cols[2].find("img")
            extra_span = cols[2].find("span", class_="opened")

            if not topic_tag:
                continue

            title = topic_tag.get_text(" ", strip=True)
            topic_url = topic_tag.get("href", "").strip()
            forum_name = forum_tag.get_text(" ", strip=True) if forum_tag else ""
            forum_url = forum_tag.get("href", "").strip() if forum_tag else ""
            author = author_tag.get_text(" ", strip=True) if author_tag else ""
            author_url = author_tag.get("href", "").strip() if author_tag else ""
            download_url = dl_tag.get("href", "").strip() if dl_tag else ""

            size_text = cols[5].get_text(" ", strip=True)
            seeders_text = cols[6].get_text(" ", strip=True)
            leechers_text = cols[7].get_text(" ", strip=True)
            replies_text = cols[8].get_text(" ", strip=True)
            added_text = cols[9].get_text(" ", strip=True)

            status_title = status_img.get("title", "").strip() if status_img else ""
            extra_text = extra_span.get_text(" ", strip=True) if extra_span else ""
            # print(f"{title}\n{topic_url}\n")
            size_text = size_text.split(" ")
            size_text = f"{size_text[1]} {size_text[2]}"
            torrent_list.append(TorrentInfo(
                category=forum_name,
                name=title,
                url=topic_url,
                # forum_url=forum_url,
                # author=author,
                # author_url=author_url,
                magnet_link=download_url,
                size=size_text,
                seeds=seeders_text,
                leeches=leechers_text,
                # replies=replies_text,
                # added=added_text,
                # status=status_title,
                # extra=extra_text,
            ))

        return torrent_list

    def get_tracker_list(self, search_request: str) -> list[ABCTorrentInfo]:
        list_ = _retries_retry_operation(self.__get_search_list, search_request, self.__search_url)
        if list_:
            return list_
        else:
            return [TorrentInfo(name="Ошибка поиска. Попробуйте снова")]


class NmClubParserPage:
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

    def get_other_data(self) -> list:
        self.__load_page()
        if self.__soup:
            data = []

            post = self.__soup.select_one("div.postbody")
            if not post:
                return data

            # все жирные заголовки
            keys = post.select("span[style*='font-weight: bold']")

            for key_tag in keys:
                key = key_tag.get_text(strip=True).rstrip(":")

                value_parts = []

                # идём по соседям после ключа
                for node in key_tag.next_siblings:

                    # остановка на следующем ключе
                    if getattr(node, "name", None) == "span" and \
                            "font-weight: bold" in node.get("style", ""):
                        break

                    if getattr(node, "name", None) == "br":
                        continue

                    text = getattr(node, "get_text", lambda **_: str(node))(
                        strip=True
                    )
                    if text:
                        value_parts.append(text)
                value = " ".join(value_parts).strip()
                if value:
                    data.append([key, value])
            return data
        return [['', "Ошибка: Не удалось загрузить контент с  NnmClub"]]


if __name__ == '__main__':
    p = NmClub().get_tracker_list("Повелитель тайн")

    print(p[0].size, p[0].name, p[0].get_magnet, p[0].get_other_data)

    # print("POST status:", r.status_code)
    # print("final url:", r.url)
    # print("request body sent:", r.request.body)
    # print("title present:", "<title>Трекер :: NNM-Club</title>" in r.text)
    # print("results present:", "Результатов поиска:" in r.text)
    # print("query present:", "Повелитель тайн" in r.text)
    #
    # print(r.text[:3000])