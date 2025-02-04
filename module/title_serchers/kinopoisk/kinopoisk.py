import requests
import time
from module.crypto_token import config
from typing import List, Tuple


def _retries_retry_operation(func, *args, retries: int = 5, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Попытка {attempt + 1} из {retries}. Ошибка сети: ПОДКЛЮЧЕНИЯ Rutracker {e}.")
            time.sleep(0.3)
    print(f"Не удалось загрузить kinopoisk после {retries} попыток.")
    return None


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


@singleton
class KinopoiskDatabaseSearch:
    def __init__(self):
        self.__BASE_URL = "https://api.kinopoisk.dev/v1.4/movie/search"
        self.__headers = {
            "X-API-KEY": config.API_TOKEN_KINOPOISK,  # API-ключ
            "Accept": "application/json"
        }

    def find_id_titles_id_by_request(self, search_title: str) -> Tuple[int, int]:
        """
        Find the titles ID by search title.
        :return: best_score: int, best_match: int -> id
        """

        pass

    def get_titles_by_id(self, aid) -> List[Tuple[str, str, str]]:
        """
        Get titles by anidb id.
        :param aid: The ID of the anime.
        :return: A list of tuple containing three strings:
                 - Title
                 - Language
                 - Type (Official, Unofficial, etc...)
        """
        pass

    def get_names_and_url_title(self, search_request: str) -> (List[str], str, str):
        """
        Get name title by search request.
        :param search_request: search request.
        :return: A tuple containing :
                 - 2-3 most popular names
                 - url
                 - resours url
        """
        params = {
            "query": search_request,  # Поисковый запрос
            "limit": 1,  # Количество результатов на странице
            "page": 1    # Номер страницы
        }
        response = _retries_retry_operation(requests.get, self.__BASE_URL, params=params, headers=self.__headers)
        url_ = ''
        if response.status_code == 200:
            data = response.json()
            for movie in data.get("docs", []):  # Перебираем найденные фильмы/сериалы
                kino_name = movie.get('name')
                kino_type_ = movie.get('type')
                kino_id = movie.get('id')
                ex_id = movie.get('externalId')
                imdb_str = ''
                if ex_id:
                    imdb_id = ex_id.get('imdb')
                    if imdb_id:
                        imdb_str = f'\n[IMDb](https://www.imdb.com/title/{imdb_id}/)'

                if kino_type_ in ['animated-series', 'tv-series']:
                    url_ = f'https://www.kinopoisk.ru/series/{kino_id}/'
                elif kino_type_ in ['cartoon', 'movie']:
                    url_ = f'https://www.kinopoisk.ru/film/{kino_id}/'

                return ([kino_name], f'[Кинопоиск]({url_}){imdb_str}')

        else:
            print(f"Ошибка {response.status_code}: {response.text}")
            return (["Ошибка"], "Кинопоиск")



if __name__ == '__main__':
    p = Kinopoisk().get_names_and_url_title("Холоп. Великолепный век (2024)")
