from .ABC import ABCDatabaseSearch
from typing import List, Tuple
from module.crypto_token import config

class ManagerDB:
    '''
    Класс ManagerDB управляет списком баз данных и предоставляет метод для поиска информации по заданным категориям и названию.
    Атрибуты:
    __list_db: List[Tuple[ABCDatabaseSearch, str]] — список кортежей, где:
        ABCDatabaseSearch — экземпляр класса, реализующего поиск в базе данных.
        str — категория, соответствующая данной базе данных.
    '''
    def __init__(self, list_db: List[Tuple[ABCDatabaseSearch, str]]):
        '''
        :param list_db: List[Tuple[ABCDatabaseSearch, categories: str = categories in MEDIA_EXTENSIONS]]
        '''
        self.__list_db: List[Tuple[ABCDatabaseSearch, str]] = list_db


    def get_info_text_and_names(self, categories: list, search_title: str) -> (str, str):
        """
    Возвращает текст с возможными вариантами названий и их URL, а также первый найденный вариант названия.

    Параметры:
        categories: list — список категорий, по которым производится поиск.
        search_title: str — строка поиска.`

        """
        add_text = []
        names = ['']
        for db in self.__list_db:
            if any(cat == db[1] for cat in categories):
                names, url_str = db[0].get_names_and_url_title(search_title)
                suggestions = "`\n - `".join(names)
                add_text.append(f"----------------------------------------\n"
                                f"**Возможно вы имели в виду {db[1]}:** \n - `{suggestions}`\n"
                                f"{url_str}\n")
        add_text.append("----------------------------------------")
        return ''.join(add_text), names[0]

