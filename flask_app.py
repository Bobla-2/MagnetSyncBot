from threading import RLock
from soupsieve.util import lower
from telegram_app import Client
from flask import Flask, jsonify, render_template, request
from module.logger.logger import SimpleLogger
from module.crypto_token import config
import secrets
from flask import make_response
import time
from module.torrent_tracker.BD_offline.bd_offline import TorrentSQLiteCache


logger = SimpleLogger()
app = Flask(__name__)
_last_error = ""
_clients_by_id = {}
_clients_lock = RLock()
torrent_dowlander_lock = RLock()
_CLIENT_TTL = 10000
_downloads_cache = {
    "ts": 0.0,
    "items": [],
    "space_info": "NA"
}

CLIENT_COOKIE_NAME = "magnetsync_client_id"

class WebClient(Client):
    def __init__(self):
        self.lock = RLock()
        self._in_lock = RLock()
        self.last_active = ''
        self.__bd = TorrentSQLiteCache() if "local" in list(map(lower, config.TRACKERS)) else None
        super().__init__()

    def web_prepare_search_meta(self) -> None:
        if not self.list_torrent_info:
            self.true_name_jellyfin = ''
            return
        categories = [torrent_info.short_category for torrent_info in self.list_torrent_info]
        db_data = self.db_manager.get_info_text_and_names(
            categories,
            self.last_search_title
        )
        if db_data:
            self.true_name_jellyfin = db_data[0][1][0]

    def web_get_search_results(self) -> list[dict]:
        out = []
        if not self.list_torrent_info:
            return out
        for num, torrent_info in enumerate(self.list_torrent_info):
            data = {
                "Категория": torrent_info.short_category,
            }
            if torrent_info.size:
                data["Вес"] = torrent_info.size
            if torrent_info.short_category == "anime":
                data["Сезон"] = str(torrent_info.season)
                if torrent_info.qualiti:
                    data["Качество"] = str(torrent_info.qualiti)

            elif torrent_info.short_category == "music":
                data["Кодек"] = str(torrent_info.qualiti)

            elif torrent_info.short_category == "cinema":
                data["Качество"] = str(torrent_info.qualiti)
            enable_magnet = torrent_info.enable_magnet
            out.append({
                "num": num,
                "name": torrent_info.name[:130],
                "data": data,
                "enable_magnet": enable_magnet,
            })
        return out

    def web_start_download(self, num: int, other: str | None = None, arg_param: str | None = None) -> None:
        SimpleLogger().log(f"[WebClient] : num={num}, other={other}, arg_param={arg_param}")
        if not self.torrent_client:
            raise RuntimeError("Ошибка подключения к торрент клиенту")
        if num < 0 or num >= self.get_torrent_info_list_len():
            raise ValueError(f"Номер {num} отсутствует")

        self.start_download_torrent(num)
        if not self.selected_torrent_info.id_torrent:
            raise RuntimeError("Не удалось добавить торрент в клиент")

        if other == 'jl':
            self.create_symlink(num, arg_param=arg_param)

        if self.__bd:
            torrent = self.list_torrent_info[num]
            self.__bd.save_full(
                url=torrent.url,
                magnet=torrent.get_magnet,
                other_data=torrent.get_other_data
            )

    def get_free_space(self):
        if not self.torrent_client:
            return "NA"
        free_space = self.torrent_client.free_spase()
        if not free_space:
            return "NA"
        out = ''
        for sp in free_space:
            out += f"{sp:.1f}/"
        out = f"{out[:-1]}TB"
        return out


    def web_get_active_torrents(self) -> list[dict]:
        if not self.torrent_client:
            return []
        self.get_list_active_torrent()
        out = []
        if not self.list_active_torrent:
            return out
        for num, torrent in enumerate(self.list_active_torrent):
            out.append({
                "num": num,
                "id": torrent.id,
                "name": torrent.name,
                "status": torrent.status,
                "progress": torrent.progress,
            })
        return out

    def get_list_active_torrent(self) -> None:
        if not self.torrent_client:
            self.list_active_torrent = []
            return
        self.list_active_torrent = self.torrent_client.get_list_active_torrents()

    def get_full_info_torrent(self, num: int) -> str:
        if not self.list_torrent_info or num < 0 or num >= len(self.list_torrent_info):
            return "Ничего не найдено"

        with self._in_lock:
            torrent = self.list_torrent_info[num]
            data = torrent.get_other_data
            if self.__bd:
                self.__bd.save_full(torrent.url, torrent.get_magnet, data)

        lines = []
        current_length = 0
        for key, value in data:
            line = f"{key}: {value}"
            lines.append(line)
            current_length += len(line)
            if current_length > 1950:
                break

        return "\n".join(lines) + "\n"

    def get_default_path_jellyfin(self, num: int) -> str:
        if not self.list_torrent_info or num < 0 or num >= len(self.list_torrent_info):
            return ""

        torrent = self.list_torrent_info[num]
        base_path = self.true_name_jellyfin
        if torrent.short_category == "anime":
            # Форматируем сезон с ведущим нулем (например, Season 01)
            return f"{base_path}/Season {self.list_torrent_info[num].season:02d}"

        return base_path


cln_for_dwns = WebClient()

def build_web_client():
    return WebClient()

def get_or_create_client_id():
    client_id = request.cookies.get(CLIENT_COOKIE_NAME)
    if client_id:
        return client_id, False

    client_id = secrets.token_hex(16)
    return client_id, True

def get_client_by_request():
    client_id, is_new = get_or_create_client_id()
    with _clients_lock:
        client = _clients_by_id.get(client_id)
        if client is None:
            client = WebClient()
            _cleanup_old_clients()
            _clients_by_id[client_id] = client
    client.last_active = time.time()
    return client, client_id, is_new

def _cleanup_old_clients():
    # Удалять клиентов, которые не использовались > TTL
    now = time.time()
    expired = [cid for cid, cl in _clients_by_id.items() if now - cl.last_active > _CLIENT_TTL]
    for cid in expired:
        del _clients_by_id[cid]

def make_json_response(payload: dict, client_id: str = None, is_new: bool = False, status: int = 200):
    response = make_response(jsonify(payload), status)

    if is_new and client_id:
        response.set_cookie(
            CLIENT_COOKIE_NAME,
            client_id,
            httponly=True,
            samesite="Lax",
        )
    return response


@app.route("/")
def index():
    return render_template("index.html", tracker_options=config.TRACKERS)

@app.get("/api/search/last")
def api_search_last():
    global _last_error
    try:
        client, client_id, is_new = get_client_by_request()
        with client.lock:
            items = client.web_get_search_results()
            jl_name = client.get_default_name_jellyfin()
            query = getattr(client, "last_search_title", "") or ""

        return make_json_response({
            "ok": True,
            "items": items,
            "default_name_jellyfin": jl_name,
            "count": len(items),
            "query": query,
        }, client_id, is_new)

    except Exception as e:
        _last_error = str(e)
        logger.log(f"[WEB] api_search_last: {e}")
        return jsonify({"ok": False, "error": "Ошибка чтения прошлых результатов"}), 500

@app.post("/api/search")
def api_search():
    global _last_error

    data = request.get_json(silent=True) or {}
    query = str(data.get("query", "")).strip()
    tracker = str(data.get("tracker", "all")).strip()

    if not query:
        return jsonify({"ok": False, "error": "Пустой поисковый запрос"}), 400

    try:
        client, client_id, is_new = get_client_by_request()
        with client.lock:
            client.search_torrent(query, tracker)
            client.web_prepare_search_meta()

            items = client.web_get_search_results()
            jl_name = client.get_default_name_jellyfin()

        if  items and "Ошибка поиска. Попробуйте снова" in items[0].get("name"):
            items = []
        return make_json_response({
            "ok": True,
            "items": items,
            "default_name_jellyfin": jl_name,
            "count": len(items),
        }, client_id, is_new)

    except Exception as e:
        client, client_id, is_new = get_client_by_request()
        _last_error = str(e)
        logger.log(f"[WEB] api_search: {e}")
        return make_json_response({
            "ok": True,
            "items": [{"name" : f"Произошла критическая ошибка: {e}",
                       "data": {}, "num" : "0", "enable_magnet": False}],
            "default_name_jellyfin": "",
            "count": 1,
        }, client_id, is_new)

@app.get("/api/torrent/<int:num>/info")
def api_torrent_info(num: int):
    global _last_error

    try:
        client, client_id, is_new = get_client_by_request()
        with client.lock:
            if num < 0 or num >= client.get_torrent_info_list_len():
                return jsonify({"ok": False, "error": f"Номер {num} отсутствует"}), 400

            info = client.get_full_info_torrent(num)
            jl_name = client.get_default_name_jellyfin()

        return make_json_response({
            "ok": True,
            "name": client.list_torrent_info[num].name[:160],
            "info": info,
            "url": client.list_torrent_info[num].url,
            "default_name_jellyfin": jl_name,
            "enable_magnet": client.list_torrent_info[num].enable_magnet,
        }, client_id, is_new)

    except Exception as e:
        _last_error = str(e)
        logger.log(f"[WEB] api_torrent_info: {e}")
        return jsonify({"ok": False, "error": "Ошибка получения информации"}), 500


@app.post("/api/download")
def api_download():
    global _last_error

    data = request.get_json(silent=True) or {}
    try:
        num = int(data.get("num"))
    except Exception:
        return jsonify({"ok": False, "error": "Поле num должно быть числом"}), 400
    mode = str(data.get("mode", "normal")).strip()
    name_path = data.get("name_path")

    try:
        with torrent_dowlander_lock:
            client, client_id, is_new = get_client_by_request()
            with client.lock:
                client.web_start_download(
                    num=num,
                    other='jl' if mode == 'jl' else None,
                    arg_param=name_path
                )
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        _last_error = str(e)
        logger.log(f"[WEB] api_download: {e}")
        return jsonify({"ok": False, "error": "Ошибка запуска скачивания"}), 500


@app.post("/api/download/delete")
def api_download_delete():
    global _last_error

    try:
        data = request.get_json(silent=True) or {}
        id = data.get("id")
        if id is None:
            return jsonify({"ok": False, "error": "Не указан номер"}), 400
        else:
            # client, _, _ = get_client_by_request()
            with torrent_dowlander_lock:
                cln_for_dwns.delete_torrent_to_id(id)
            return jsonify({"ok": True})
    except Exception as e:
        _last_error = str(e)
        logger.log(f"[WEB] api_download_delete: {e}")
        return jsonify({"ok": False, "error": "Ошибка удаления закачки"}), 500


@app.get("/api/downloads")
def api_downloads():
    global _last_error, _downloads_cache
    now = time.time()
    try:
        with torrent_dowlander_lock:
            if (now - _downloads_cache["ts"]) < 5:
                items = _downloads_cache["items"]
                space_info = _downloads_cache["space_info"]
            else:
                items = cln_for_dwns.web_get_active_torrents()
                space_info = cln_for_dwns.get_free_space()
                _downloads_cache["items"] = items[:50]
                _downloads_cache["ts"] = now
                _downloads_cache["space_info"] = space_info

        return jsonify({
            "ok": True,
            "items": items,
            "space_info": space_info,
            "count": len(items),
        })

    except Exception as e:
        _last_error = str(e)
        logger.log(f"[WEB] api_downloads: {e}")
        return jsonify({"ok": False, "error": "Ошибка чтения списка закачек"}), 500

@app.post("/api/default_path")
def api_default_path():
    global _last_error
    try:
        data = request.get_json(silent=True) or {}
        num = int(data.get("num"))
    except Exception:
        return jsonify({"ok": False, "error": "Поле num должно быть числом"}), 400

    try:
        client, client_id, is_new = get_client_by_request()
        with client.lock:
            if num < 0 or num >= client.get_torrent_info_list_len():
                return jsonify({"ok": False, "error": f"Номер {num} отсутствует"}), 400

            default_path = client.get_default_path_jellyfin(num)

        return make_json_response({
            "ok": True,
            "default_path": default_path,
        }, client_id, is_new)

    except Exception as e:
        _last_error = str(e)
        logger.log(f"[WEB] api_downloads: {e}")
        return jsonify({"ok": False, "error": "Ошибка чтения списка закачек"}), 500

@app.get("/api/last_error")
def api_last_error():
    log_text = logger.get_log_text() or ""
    return jsonify({
        "ok": True,
        "error": log_text or "",
    })


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8080, debug=True)
