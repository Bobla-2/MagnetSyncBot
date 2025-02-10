import os
import pickle
import gzip
import requests
from xml.dom.minidom import parse
from fuzzywuzzy import fuzz
from typing import List, Tuple
from module.crypto_token.config import proxy
from ..ABC import ABCDatabaseSearch
import re
from datetime import datetime, timedelta



def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


@singleton
class AnimeDatabaseSearch(ABCDatabaseSearch):
    def __init__(self):
        self.__data_create = None
        self.__anime_list = AnimeDatabaseLoader().load_or_parse_database()

    def find_id_titles_id_by_request(self, search_title: str):
        """Find the anime ID by title using fuzzy matching."""
        best_match = None
        best_score = 0

        for anime in self.__anime_list:
            for title in anime['titles']:
                similarity_score = fuzz.ratio(search_title.lower(), title['title'].lower())

                if similarity_score > best_score:
                    best_score = similarity_score
                    best_match = anime['aid']
        return best_score, best_match

    def get_titles_by_id(self, aid) -> List[Tuple[str, str, str]]:
        """
        Get titles by anidb id.
        :param aid: The ID of the anime.
        :return: A list of tuple containing three strings:
                 - Title
                 - Language
                 - Type (Official, Unofficial, etc...)
        """
        for anime in self.__anime_list:
            if anime['aid'] == aid:
                return [(title['title'], title['lang'], title['type']) for title in anime['titles']]
        return []

    def get_names_and_url_title(self, search_title: str) -> (List[str], str):
        if self.__check_creation_date():
            AnimeDatabaseLoader().update_database()
            self.__anime_list = AnimeDatabaseLoader().load_or_parse_database()
            self.__data_create = AnimeDatabaseLoader().get_dat()
        _, anime_id = self.find_id_titles_id_by_request(search_title)
        list_ = self.get_titles_by_id(anime_id)
        return ([title[0] for title in list_
                if title[2] in 'main']+[
                title[0] for title in list_
                if title[1] == 'ru' and title[2] in ('main', 'syn', 'official')],
                f'[AniDB](https://anidb.net/anime/{anime_id})')

    def __check_creation_date(self, len_days=14):
        if not self.__data_create:
            self.__data_create = AnimeDatabaseLoader().get_dat()

        if self.__data_create:
            current_time = datetime.now()
            if current_time - self.__data_create > timedelta(days=len_days):
                print(f"Прошло больше 14 дней с создания XML. Дата создания: {self.__data_create}")
                return True
            else:
                print(f"С момента создания XML прошло меньше 14 дней. Дата создания: {self.__data_create}")
        else:
            print("Не удалось найти дату создания в XML.")
        return False


class AnimeDatabaseLoader:
    def __init__(self):
        cache_dir = '.cache'
        os.makedirs(cache_dir, exist_ok=True)

        self.__xml_file_path = os.path.join(cache_dir, 'anime-titles.xml')
        self.__cache_file_path = os.path.join(cache_dir, 'anime_list_cache.pkl')
        self.__gz_file_path = os.path.join(cache_dir, 'anime-titles.xml.gz')

    def update_database(self):
        self.__download_database_xml()
        self.__update_cache_from_xml()

    def load_or_parse_database(self):
        """Load the anime list from cache if it exists; otherwise, parse the XML file and create the cache."""
        if not os.path.exists(self.__cache_file_path):
            print("Cache not found. Parsing XML file...")
            if not self.__update_cache_from_xml():
                print("XML file parse error, downloading...")
                self.__download_database_xml()
                self.__update_cache_from_xml()

        with open(self.__cache_file_path, 'rb') as f:
            return pickle.load(f)


    def get_dat(self):
        try:
            with open(self.__xml_file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()  # Читаем файл построчно с конца

            for line in reversed(lines):  # Ищем комментарий с конца файла
                match = re.search(r"<!-- Created:\s*(.*?)\s*\(", line)
                if match:
                    date_str = match.group(1)
                    return datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')
                return None
        except Exception as e:
            print(f"Ошибка при обработке XML: {e}")
            return None

    def __parse_xml_file(self):
        """Parse the XML file and return a list of anime."""
        if not os.path.exists(self.__xml_file_path):
            print(f"The XML file does not exist: {self.__xml_file_path}")
            return None

        anime_list = []
        with open(self.__xml_file_path, 'r', encoding='utf-8') as file:
            dom = parse(file)

            target_languages = {'x-jat', 'en', 'ru'}

            for anime in dom.getElementsByTagName('anime'):
                aid = anime.getAttribute('aid')
                titles = [
                    {
                        'title': title.firstChild.data,
                        'lang': title.getAttribute('xml:lang'),
                        'type': title.getAttribute('type')
                    }
                    for title in anime.getElementsByTagName('title')
                    if title.getAttribute('xml:lang') in target_languages and title.firstChild]

                if titles:
                    anime_list.append({'aid': aid, 'titles': titles})
        return anime_list

    def __update_cache_from_xml(self):
        """Manually update the cache by re-parsing the XML file and saving the new data."""
        if (anime_list := self.__parse_xml_file()) is None:
            return False

        with open(self.__cache_file_path, 'wb') as f:
            pickle.dump(anime_list, f)
        return True

    def __download_database_xml(self, url='http://anidb.net/api/anime-titles.xml.gz'):
        """Update the database by downloading the XML file, extracting it, and updating the cache."""
        print("Downloading the XML file...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            proxies = {'http': proxy,
                       'https': proxy}
            response = requests.get(url, headers=headers, proxies=proxies)
            if response.status_code == 200:
                with open(self.__gz_file_path, 'wb') as f:
                    f.write(response.content)
                print("Download complete. Extracting the XML file...")

                with gzip.open(self.__gz_file_path, 'rb') as f_in:
                    with open(self.__xml_file_path, 'wb') as f_out:
                        f_out.write(f_in.read())
            else:
                print(f"Failed to download file. Status code: {response.status_code}")

        except requests.RequestException as e:
            print(f"An error occurred: {e}")


if __name__ == '__main__':
    db = AnimeDatabaseSearch()
    search_title = "Crest the"
    _, anime_id = db.find_id_titles_id_by_request(search_title)
    print(f"Anime ID for title '{search_title}':", anime_id)
    print(db.get_titles_by_id(anime_id))

