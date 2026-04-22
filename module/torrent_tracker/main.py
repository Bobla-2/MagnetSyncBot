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
        if "1337" in resource and self.__x1337:
            data = self.__x1337.get_tracker_list(title)
        elif "rutracker" in resource and self.__rutecker:
            data = self.__rutecker.get_tracker_list(title)
        elif "anilibria" in resource and self.__anilibria:
            data = self.__anilibria.get_tracker_list(title)
        elif "anidub" in resource and self.__anidub:
            data = self.__anidub.get_tracker_list(title)
        elif "nnmclub" in resource and self.__nmclub:
            data = self.__nmclub.get_tracker_list(title)
        elif "local" in resource and self.__local:
            return self.__local.get_tracker_list(title)
        else:
            raise Exception(f"[TorrentTracker] : трекера не существует: {resource}")

        if self.__bd and data:
            if len(data) == 1 and re.search( r"(?i)\b(ошибк\w*|не найдено)\b", data[0].name):
                pass
            else:
                self.__bd.save_fast(data)
        return data
