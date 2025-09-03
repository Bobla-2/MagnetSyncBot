from module.torrent_tracker.rutracker.rutrecker import Rutracker
from module.torrent_tracker.x1337.x1337 import X1337
from module.torrent_tracker.anilibria.anilibria import Anilibria
from module.torrent_tracker.AniDub.anidub import AniDub
from module.torrent_tracker.TorrentInfoBase import ABCTorrentInfo


class TorrentTracker:
    def __init__(self):
        self.__rutecker = Rutracker()
        self.__x1337 = X1337()
        self.__anilibria = Anilibria()
        self.__anidub = AniDub()

    def get_tracker_list(self, title: str, resource: str) -> list[ABCTorrentInfo]:
        resource = resource.lower()
        if "1337" in resource:
            return self.__x1337.get_tracker_list(title)
        elif "rutracker" in resource:
            return self.__rutecker.get_tracker_list(title)
        elif "anilibria" in resource:
            return self.__anilibria.get_tracker_list(title)
        elif "anidub" in resource:
            return self.__anidub.get_tracker_list(title)
        else:
            return self.__rutecker.get_tracker_list(title)

