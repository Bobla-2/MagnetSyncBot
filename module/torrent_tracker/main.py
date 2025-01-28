from module.torrent_tracker.rutracker.rutrecker import Rutracker
from module.torrent_tracker.x1337.x1337 import X1337
from module.torrent_tracker.TorrentInfoBase import AbstractTorrentInfo



class TorrentTracker:
    def __init__(self):
        self.__rutecker = Rutracker()
        self.__x1337 = X1337()

    def get_tracker_list(self, title: str) -> [AbstractTorrentInfo]:
        if title.split()[0] == "1337":
            return self.__x1337.get_tracker_list(title[5:])
        else:
            return self.__rutecker.get_tracker_list(title)

