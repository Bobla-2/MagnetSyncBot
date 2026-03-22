from threading import Lock
from telegram_app import Client
from flask import Flask, jsonify, render_template, request
from module.logger.logger import SimpleLogger
from module.crypto_token import config
import secrets
from flask import make_response


# config.JELLYFIN_ENABLE = False

_clients_by_id = {}
_clients_lock = Lock()

CLIENT_COOKIE_NAME = "magnetsync_client_id"

class WebClient(Client):
    def __init__(self):
        super().__init__()

    def web_prepare_search_meta(self) -> None:
        if not self.list_torrent_info:
            self.true_name_jellyfin = ''
            return

        categories = [torrent_info.short_category for torrent_info in self.list_torrent_info]
        _, self.true_name_jellyfin = self.db_manager.get_info_text_and_names(
            categories,
            self.last_search_title
        )

    def web_get_search_results(self) -> list[dict]:
        out = []
        if not self.list_torrent_info:
            return out

        for num, torrent_info in enumerate(self.list_torrent_info):
            out.append({
                "num": num,
                "name": torrent_info.name,
                "size": torrent_info.size,
                "category": torrent_info.short_category,
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
        if not self.list_torrent_info:
            return "Ничего не найдено"
        data = self.list_torrent_info[num].get_other_data

        data_str = []
        current_length = 0
        for dt in data:
            string = f"{dt[0]}: {dt[1]}"
            data_str.append(string)
            current_length += len(string)
            if current_length > 1950:
                break
        res = "\n".join(data_str)
        return (f"{res}\n")

logger = SimpleLogger()


def build_web_client():
    return WebClient()
    """
    Здесь нужно вернуть ТВОЙ ГОТОВЫЙ client.
    Именно тот, через который у тебя уже работает поиск/скачивание.

    Пример:
        return BotClient(...)

    или:
        return some_factory.create_client(...)
    """
    raise NotImplementedError("Подставь здесь создание своего client")




app = Flask(__name__)

_client_lock = Lock()
_client = None
_last_error = ""

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
            _clients_by_id[client_id] = client

    return client, client_id, is_new

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

def get_client():
    global _client

    if _client is None:
        _client = build_web_client()

    return _client


@app.route("/")
def index():
    return render_template("index.html", tracker_options=config.TRACKERS)


@app.get("/api/search/last")
def api_search_last():
    global _last_error

    try:
        with _client_lock:
            client, client_id, is_new = get_client_by_request()
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
        with _client_lock:
            client, client_id, is_new = get_client_by_request()
            client.search_torrent(query, tracker)
            client.web_prepare_search_meta()
            items = client.web_get_search_results()
            jl_name = client.get_default_name_jellyfin()

        return make_json_response({
            "ok": True,
            "items": items,
            "default_name_jellyfin": jl_name,
            "count": len(items),
        }, client_id, is_new)

    except Exception as e:
        _last_error = str(e)
        logger.log(f"[WEB] api_search: {e}")
        return jsonify({"ok": False, "error": "Ошибка поиска"}), 500


@app.get("/api/torrent/<int:num>/info")
def api_torrent_info(num: int):
    global _last_error

    try:
        client, client_id, is_new = get_client_by_request()

        with _client_lock:
            if num < 0 or num >= client.get_torrent_info_list_len():
                return jsonify({"ok": False, "error": f"Номер {num} отсутствует"}), 400

            info = client.get_full_info_torrent(num)
            jl_name = client.get_default_name_jellyfin()

        return make_json_response({
            "ok": True,
            "name": client.list_torrent_info[num].name,
            "info": info,
            "url": client.list_torrent_info[num].url,
            "default_name_jellyfin": jl_name,
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
        with _client_lock:
            client, client_id, is_new = get_client_by_request()
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
        num = data.get("num", None)

        if num is None:

            return jsonify({"ok": False, "error": "Не указан номер"}), 400

        with _client_lock:
            client = get_client()
            client.delete_torrent(num)

        return jsonify({"ok": True})
    except Exception as e:
        _last_error = str(e)
        logger.log(f"[WEB] api_download_delete: {e}")
        return jsonify({"ok": False, "error": "Ошибка удаления закачки"}), 500


@app.get("/api/downloads")
def api_downloads():
    global _last_error
    try:
        with _client_lock:
            client, client_id, is_new = get_client_by_request()
            items = client.web_get_active_torrents()

            return make_json_response({
                "ok": True,
                "items": items,
                "count": len(items),
            }, client_id, is_new)
    # try:
    #     with _client_lock:
    #         client = get_client()
    #         items = client.web_get_active_torrents()
    #
    #     return jsonify({
    #         "ok": True,
    #         "items": items,
    #         "count": len(items),
    #     })
    except Exception as e:
        _last_error = str(e)
        logger.log(f"[WEB] api_downloads: {e}")
        return jsonify({"ok": False, "error": "Ошибка чтения списка закачек"}), 500


@app.get("/api/last_error")
def api_last_error():
    return jsonify({
        "ok": True,
        "error": _last_error,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)