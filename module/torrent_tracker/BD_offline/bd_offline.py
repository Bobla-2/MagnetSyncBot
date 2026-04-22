import sqlite3
import json
import time

from module.torrent_tracker.TorrentInfoBase import ABCTorrentInfo
from module.other.singleton import singleton
from module.crypto_token.config import BD_PATH
from threading import RLock


@singleton
class TorrentSQLiteCache:
    def __init__(self, db_path: str = BD_PATH):
        self.lock = RLock()
        self.conn = sqlite3.connect(db_path,
                                    check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS torrents (
                url TEXT PRIMARY KEY,
    
                -- FAST DATA
                name TEXT,
                size TEXT,
                seeds INTEGER,
                leeches INTEGER,
                year TEXT,
                category TEXT,
                short_category TEXT,
                qualiti TEXT,
    
                -- FULL DATA
                magnet TEXT,
                other_data TEXT,
    
                -- timestamps
                cached_at_fast INTEGER,
                cached_at_full INTEGER
            )
            """)

            cur.execute("CREATE INDEX IF NOT EXISTS idx_name ON torrents(name)")

            self.conn.commit()

    # ----------------------------
    # SAVE
    # ----------------------------
    def save_fast(self, torrents: list[ABCTorrentInfo]):
        with self.lock:
            cursor = self.conn.cursor()
            now = int(time.time())

            for t in torrents:
                cursor.execute("""
                INSERT INTO torrents (
                    url, name, size, seeds, leeches,
                    year, category, short_category, cached_at_fast, qualiti 
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    name=excluded.name,
                    size=excluded.size,
                    seeds=excluded.seeds,
                    leeches=excluded.leeches,
                    year=excluded.year,
                    category=excluded.category,
                    short_category=excluded.short_category,
                    cached_at_fast=excluded.cached_at_fast,
                    qualiti = excluded.qualiti
                """, (
                    t.url,
                    t.name,
                    t.size,
                    int(getattr(t, "_TorrentInfo__seeds", 0)),
                    int(getattr(t, "_TorrentInfo__leeches", 0)),
                    str(getattr(t, "_TorrentInfo__year", "")),
                    getattr(t, "_TorrentInfo__category", ""),
                    t.short_category,
                    now,
                    getattr(t, "_TorrentInfo__qualiti", "")
                ))
            self.conn.commit()

    def save_full(self, url: str, magnet: str, other_data: list):
        with self.lock:
            cur = self.conn.cursor()
            now = int(time.time())

            cur.execute("""
            UPDATE torrents
            SET magnet = ?,
                other_data = ?,
                cached_at_full = ?
            WHERE url = ?
            """, (
                magnet,
                json.dumps(other_data, ensure_ascii=False),
                now,
                url
            ))
            self.conn.commit()

    # ----------------------------
    # LOAD
    # ----------------------------
    def load_list(self, tracker: str, query: str) -> list[dict]:
        with self.lock:
            cursor = self.conn.cursor()

            cursor.execute("""
                SELECT *
                FROM torrents
                WHERE tracker = ?
                  AND name LIKE ?
                ORDER BY cached_at_fast DESC
                LIMIT 50
            """, (tracker, f"%{query}%"))

        return [dict(r) for r in cursor.fetchall()]

    def search(self, query: str, tracker: str = None, limit: int = 100):
        with self.lock:
            cur = self.conn.cursor()

            if tracker:
                cur.execute("""
                SELECT *
                FROM torrents
                WHERE tracker = ?
                  AND name LIKE ?
                ORDER BY cached_at_fast DESC
                LIMIT ?
                """, (tracker, f"%{query}%", limit))
            else:
                cur.execute("""
                SELECT *
                FROM torrents
                WHERE name LIKE ?
                ORDER BY cached_at_fast DESC
                LIMIT ?
                """, (f"%{query}%", limit))

        return [dict(r) for r in cur.fetchall()]

    # ----------------------------
    # CLEAR OLD CACHE
    # ----------------------------
    def clean_old(self, max_age_sec: int = 3600 * 24 * 30):
        with self.lock:
            cursor = self.conn.cursor()
            now = int(time.time())

            cursor.execute("""
                DELETE FROM torrents
                WHERE cached_at_fast < ?
            """, (now - max_age_sec,))

            self.conn.commit()

    # ----------------------------
    # utils
    # ----------------------------



class TorrentInfo(ABCTorrentInfo):
    """
    DTO объект торрента (только данные из БД / парсера).
    НИКАКОЙ сети внутри.
    """

    __slots__ = (
        '__category', '__name', '__year', '__url',
        '__id_torrent', '__size', '__seeds', '__leeches',
        '__short_categories', '__id', '__magnet', '__data',
        '__qualiti', '__season'
    )

    def __init__(self,
                 url: str = None,
                 id: int = None,
                 category: str = '',
                 name: str = None,
                 year: str = None,
                 magnet: str = None,
                 size: str = None,
                 data=None,
                 seeds: str = None,
                 leeches: str = None,
                 short_categories: str = None,
                 qualiti: str = None,
                 season: str = None):

        self.__category = category
        self.__magnet = magnet
        self.__data = data or []
        self.__id = id
        self.__name = name
        self.__year = year
        self.__url = url
        self.__size = size
        self.__seeds = seeds
        self.__leeches = leeches
        self.__id_torrent = None

        self.__short_categories = short_categories or "other"
        self.__qualiti = qualiti or ""
        self.__season = season or 1

    # -------------------------
    # CORE
    # -------------------------
    @property
    def get_magnet(self) -> str:
        return self.__magnet

    @property
    def size(self) -> str:
        return self.__size or ""

    @property
    def name(self) -> str:
        return self.__name or ""

    @property
    def url(self) -> str:
        return self.__url

    @property
    def id_torrent(self) -> str | int:
        return self.__id_torrent

    @id_torrent.setter
    def id_torrent(self, id_: str | int):
        self.__id_torrent = id_

    # -------------------------
    # DATA
    # -------------------------
    @property
    def get_other_data(self) -> list:
        """
        ВСЕ доп. данные из БД + базовые поля.
        """
        dt = [
            ["Вес", self.__size],
            # ["id", self.__id],
            ["Категория", self.__category],
            ["magnet", self.__magnet],
            # ["name", self.__name],
            ["Год", self.__year],
            # ["url", self.__url],
            ["seeds", self.__seeds],
            ["leeches", self.__leeches],
            ["short_category", self.__short_categories],
            ["Качество", self.__qualiti],

        ] + (self.__data or [])
        if self.__magnet:
            dt.append(["magnet", self.__magnet])
        if self.__season and self.__season != "-1":
            dt.insert(2, ["Сезон", self.__season])
        return dt

    # -------------------------
    # META
    # -------------------------
    @property
    def short_category(self) -> str:
        return self.__short_categories or "other"

    @property
    def season(self) -> int:
        try:
            return int(self.__season)
        except:
            return 1

    @property
    def qualiti(self) -> str:
        return self.__qualiti or ""

    @property
    def enable_magnet(self) -> bool:
        return not self.__magnet is None

    # -------------------------
    # OPTIONAL DEBUG
    # -------------------------
    def __repr__(self):
        return f"TorrentInfo(name={self.__name}, size={self.__size}, seeds={self.__seeds})"


@singleton
class LocalTorrentSearch:
    """
    Только поиск по локальной БД.
    НИКАКИХ HTTP, НИКАКИХ сохранений.
    """

    def __init__(self):
        self.cache = TorrentSQLiteCache()

    def get_tracker_list(self, query: str, limit: int = 200) -> list[TorrentInfo]:
        rows = self.cache.search(query=query, limit=limit)
        return self._to_objects(rows)

    def _to_objects(self, rows: list[dict]) -> list[TorrentInfo]:
        result = []
        for r in rows:
            result.append(
                TorrentInfo(
                    url=r.get("url"),
                    id=r.get("id"),

                    name=r.get("name"),
                    size=r.get("size"),

                    seeds=r.get("seeds"),
                    leeches=r.get("leeches"),

                    year=r.get("year"),
                    category=r.get("category"),

                    short_categories=r.get("short_category"),

                    magnet=r.get("magnet"),

                    data=json.loads(r["other_data"]) if r.get("other_data") else [],

                    qualiti=r.get("qualiti"),
                    season=r.get("season"),
                )
            )

        return result