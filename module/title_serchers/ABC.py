from abc import ABC, abstractmethod
from typing import List, Tuple


class ABCDatabaseSearch(ABC):
    @abstractmethod
    def find_id_titles_id_by_request(self, search_title: str) -> Tuple[int, int]:
        """
        Find the titles ID by search title.
        :return: best_score: int, best_match: int -> id
        """
        pass

    @abstractmethod
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

    @abstractmethod
    def get_names_and_url_title(self, search_request: str) -> (list[str], str):
        """
        Get name title by search request.
        :param search_request: search request.
        :return: A tuple containing :
                 - 2-3 most popular names
                 - url markdown style
        """
        pass


