from module.torrent_tracker.rutracker.rutrecker import Rutracker
from module.torrent_tracker.x1337.x1337 import X1337
from module.torrent_tracker.anilibria.anilibria import Anilibria
from module.torrent_tracker.AniDub.anidub import AniDub
from module.torrent_tracker.nmclub.nmclub import NmClub
from module.torrent_tracker.BD_offline.bd_offline import LocalTorrentSearch, TorrentSQLiteCache
from module.torrent_tracker.TorrentInfoBase import ABCTorrentInfo
import re


class TorrentTracker:
    def __init__(self, TRACKERS):
        TRACKERS = list(map(str.lower, TRACKERS))
        self.__x1337 = X1337() if "1337" in TRACKERS else None
        self.__rutecker = Rutracker() if "rutracker" in TRACKERS else None
        self.__anilibria = Anilibria() if "anilibria" in TRACKERS else None
        self.__anidub = AniDub() if "anidub" in TRACKERS else None
        self.__nmclub = NmClub() if "nnmclub" in TRACKERS else None
        self.__local = LocalTorrentSearch() if "local" in TRACKERS else None
        self.__bd = TorrentSQLiteCache() if "local" in TRACKERS else None


    def get_tracker_list(self, title: str, resource: str) -> list[ABCTorrentInfo]:
        resource = resource.lower()
        # Маппинг ключевых слов ресурса к соответствующим атрибутам трекеров
        trackers_map = {
            "1337": self.__x1337,
            "rutracker": self.__rutecker,
            "anilibria": self.__anilibria,
            "anidub": self.__anidub,
            "nnmclub": self.__nmclub,
            "local": self.__local
        }
        # Поиск подходящего трекера по ключу в resource
        active_tracker = None
        for key, tracker in trackers_map.items():
            if key in resource and tracker:
                active_tracker = tracker
                break
        if not active_tracker:
            raise Exception(f"[TorrentTracker] : трекера не существует: {resource}")
        data = active_tracker.get_tracker_list(title)
        if self.__bd and data:
            if len(data) == 1 and re.search( r"(?i)\b(ошибк\w*|не найдено)\b", data[0].name):
                pass
            else:
                self.__bd.save_fast(data)

        return data

