from .ABC import ABCDatabaseSearch
from typing import List, Tuple
from module.crypto_token import config

class ManagerDB:
    def __init__(self, list_db: List[Tuple[ABCDatabaseSearch, str]]):
        '''
        :param list_db: List[Tuple[ABCDatabaseSearch, categories: str = categories in MEDIA_EXTENSIONS]]
        '''
        self.__list_db: List[Tuple[ABCDatabaseSearch, str]] = list_db

    def get_info_text(self, categories: list, search_title: str) -> str:
        add_text = []
        for db in self.__list_db:
            if any(cat == db[1] for cat in categories):
                names, url_str = db[0].get_names_and_url_title(search_title)
                suggestions = "`\n - `".join(names)
                add_text.append(f"----------------------------------------\n"
                                f"**Возможно вы имели в виду:**\n - `{suggestions}`\n"
                                f"{url_str}\n")
        add_text.append("----------------------------------------")
        return ''.join(add_text)

