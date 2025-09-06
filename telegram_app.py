from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.error import NetworkError
from module.torrent_manager.manager import create_manager
from module.crypto_token import config
from module.torrent_tracker.main import TorrentTracker
from module.torrent_tracker.TorrentInfoBase import ABCTorrentInfo
from module.other.jellyfin import CreaterSymlinkManager
from module.title_serchers.anidb.anidb import AnimeDatabaseSearch
from module.title_serchers.kinopoisk.kinopoisk import KinopoiskDatabaseSearch
from module.title_serchers.manager_db import ManagerDB
from typing import List, Optional
import asyncio
from module.logger.logger import SimpleLogger


class ClientStatus:
    __slots__ = ('status', 'answer_msg', 'bot_msg_id', 'num_torrents')

    def __init__(self):
        self.status = ""
        self.answer_msg = None
        self.bot_msg_id = None
        self.num_torrents: int | None = None

    def clear(self):
        self.status = ""
        self.answer_msg = None
        self.bot_msg_id = None
        self.num_torrents: int | None = None


class BotClient:
    def __init__(self, context, update: Update, torrent_settings: list = None):
        self.context = context
        self.user_states: ClientStatus = ClientStatus()
        self.search_title = ""
        self.chat_id = update.effective_chat.id
        self.user_id = update.effective_user.id

        self.tracker_type = config.TRACKERS[0]
        self.old_ready_msg_id: int | None = None

        self.tracker = TorrentTracker()
        self.x1337 = None
        self.torrent = None

        db = []
        if config.ENABLE_KINOPOISK:
            db.append((KinopoiskDatabaseSearch(), 'cinema'))
        db.append((AnimeDatabaseSearch(), 'anime'))
        self.__db_manager = ManagerDB(db)

        if torrent_settings:
            try:
                self.torrent = create_manager(
                    client_type=torrent_settings[0],
                    host=torrent_settings[1],
                    port=int(torrent_settings[2]),
                    username=torrent_settings[3],
                    password=torrent_settings[4],
                    protocol="https" if torrent_settings[2] == "443" else "http"
                    )
            except:
                pass
        else:
            self.torrent = create_manager(
                client_type=config.tornt_cli_type,
                host=config.tornt_cli_host,
                port=config.tornt_cli_port,
                username=config.tornt_cli_login,
                password=config.tornt_cli_pass,
            )

        self.__last_search_title = ""
        self.__list_torrent_info: List[ABCTorrentInfo] = []
        self.__selected_torrent_info: ABCTorrentInfo | None = None
        self.__dict_progress_bar = {}
        self.__true_name_jellyfin = ''
        self.creater_link = None
        if config.JELLYFIN_ENABLE and torrent_settings == None:
            self.creater_link = CreaterSymlinkManager()

    def search_torrent(self, search_title: str, tracker_type: str) -> None:
        self.__list_torrent_info = self.tracker.get_tracker_list(search_title, tracker_type)
        self.__last_search_title = search_title
        self.__true_name_jellyfin = ''

    def get_torrent_info_part_list(self, num_: int) -> str:
        """
        Возвращает часть списка найденных торрент-файлов, разбитого на страницы по 6 элементов.
        Args:
            num_ (int): Номер страницы (начиная с 0).
        Returns:
            str: Строка с перечислением торрентов и дополнительной информацией,
                 либо сообщение "Ничего не найдено", если список пуст.
        """
        if not self.__list_torrent_info:
            return "Ничего не найдено"
        categories = []
        items = []
        for num, torrent_info in enumerate(self.__list_torrent_info[6 * num_:6 * (num_ + 1)]):
            categories.append(torrent_info.short_category)
            items.append(f"{num + (num_ * 6)})    {torrent_info.name} || {torrent_info.size}\n\n")

        add_text, self.__true_name_jellyfin = self.__db_manager.get_info_text_and_names(categories,
                                                                                        self.__last_search_title)
        return f"{''.join(items)} {add_text}"

    def get_torrent_info_list_len(self) -> int:
        if self.__list_torrent_info:
            return len(self.__list_torrent_info)
        else:
            return 0

    def __start_download_torrent(self, num: int):
        self.__selected_torrent_info = self.__list_torrent_info[num]
        if self.torrent:
            for me in config.MEDIA_EXTENSIONS:
                if me[3] == self.__selected_torrent_info.short_category:
                    subdir = me[1]
                    if magnet := self.__selected_torrent_info.get_magnet:
                        self.__selected_torrent_info.id_torrent = self.torrent.start_download(
                            magnet,
                            subdir)


    def stop_download_torrent(self, id_torrent: int) -> None:
        self.torrent.stop_download(id_torrent)
        self.__dict_progress_bar[str(id_torrent)].stop_progress()
        self.creater_link.stop_task(str(id_torrent))

    def __start_progresbar(self, update, context, num=None):
        """
        :param num: default __selected_torrent_info progress
        """
        torrent_: ABCTorrentInfo = self.__selected_torrent_info if not num else self.__list_torrent_info[num]
        self.__dict_progress_bar[str(torrent_.id_torrent)] = ProgressBarWithBtn(
            progress_value=lambda: self.torrent.get_progress(torrent_.id_torrent),
            update=update,
            context=context,
            total_step=10,
            name=f'{torrent_.name}',
            torrent_id=torrent_.id_torrent)

    def __create_symlink(self, num: int | None = None, arg_param=None) -> None:
        if self.creater_link:
            torrent_: ABCTorrentInfo = self.__selected_torrent_info if not num else self.__list_torrent_info[num]
            if arg_param:
                name = arg_param
            else:
                name = self.__true_name_jellyfin
            if not name:
                return
            self.creater_link.create_symlink(lambda: self.torrent.get_path(torrent_.id_torrent), name,
                                               progress_value=lambda: self.torrent.get_progress(torrent_.id_torrent), id=torrent_.id_torrent)

    def start_download_with_progres_bar(self, num, update, context, other, arg_param=None):
        print(num, other, arg_param)
        self.__start_download_torrent(num)
        if self.__selected_torrent_info.id_torrent:
            self.__start_progresbar(update, context)
            if self.torrent:
                if other == 'jl':
                    self.__create_symlink(arg_param=arg_param)
                else:
                    pass

    def get_full_info_torrent(self, num: int) -> str:
        if not self.__list_torrent_info:
            return "Ничего не найдено"
        return self.__list_torrent_info[num].full_info

    def get_default_name_jellyfin(self):
        return self.__true_name_jellyfin


class TelegramBot:
    MAX_RETRIES = 6
    num_list_torrent = 0

    def __init__(self):
        self.clients: List[BotClient] = []
        self.logger = SimpleLogger()
        self.last_error_st = "Пусто"
        row_size = 3
        rep_key_tracker = [config.TRACKERS[i:i + row_size] for i in range(0, len(config.TRACKERS), row_size)]
        self.reply_markup_trackers = ReplyKeyboardMarkup(rep_key_tracker, resize_keyboard=True)

    def setup(self, token):
        self.application = Application.builder().token(token).build()
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("log", self.cmd_log_error))
        self.application.add_handler(CommandHandler("last_log", self.cmd_last_error))
        self.application.add_handler(CommandHandler("search", self.cmd_search))
        self.application.add_handler(CommandHandler("download", self.cmd_download))
        self.application.add_handler(CommandHandler("download_jl", self.cmd_download))
        self.application.add_handler(CommandHandler("look", self.cmd_look))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.user_msg))
        self.application.add_handler(CallbackQueryHandler(self.handle_menu_selection))
        self.application.add_handler(MessageHandler(filters.Sticker.ALL, self.sticker_handler))

    def error_handler(self, update, context):
        print(f'error_handler --- {context.error}')

    @staticmethod
    def get_reply_markup(client: BotClient):
        rep_keyboard = [
            ["🔍 Поиск", f"📦 Трекер: {client.tracker_type}"]
        ]
        return ReplyKeyboardMarkup(rep_keyboard, resize_keyboard=True)

    def run(self):
        self.application.run_polling(timeout=5, poll_interval=1)

    @staticmethod
    def get_keyboard_list_torrents(next_: bool, prev: bool, begin: int = 0, end: int = 0) -> list:
        if next_ and not prev:
            keyboard_list = [
                [InlineKeyboardButton("next   ->", callback_data="next")],
            ]
        elif not next_ and prev:
            keyboard_list = [
                [InlineKeyboardButton("<-   prev", callback_data="prev")],
            ]
        elif next_ and prev:
            keyboard_list = [[
                InlineKeyboardButton("<-   prev", callback_data="prev"),
                InlineKeyboardButton("next   ->", callback_data="next")

            ]]
        else:
            keyboard_list = []

        bt_h = 2
        if config.JELLYFIN_ENABLE:
            bt_h = 3

        buttons = []
        for i in range(begin, end + 1):
            buttons.append(InlineKeyboardButton(f"🔎{i}", callback_data=f"infolook_{i}"))
            buttons.append(InlineKeyboardButton(f"⬇️{i}", callback_data=f"download_{i}"))
            if config.JELLYFIN_ENABLE:
                buttons.append(InlineKeyboardButton(f"🔗{i}", callback_data=f"ljsimlink_{i}"))
        for i in range(bt_h):
            keyboard_list.append([buttons[j] for j in range(i, len(buttons) - bt_h + i, bt_h)])

        return keyboard_list

    def __get_client_by_chat_id(self, chat_id: int) -> Optional[BotClient]:
        for client in self.clients:
            if client.chat_id == chat_id:
                return client
        return None

    async def sticker_handler(self, update: Update, context) -> None:
        """Игнорирует стикеры, чтобы бот не зависал."""
        chat_id = update.effective_chat.id
        await self.send_message_whit_try(context=context, chat_id=chat_id,
                                         text="Стикер это не команда")

    async def cmd_help(self, update: Update, context) -> None:
        chat_id = update.effective_chat.id
        await self.send_message_whit_try(context=context, chat_id=chat_id, parse_mode="Markdown",
                                         text="Для начала введите: /start {None|pass}\n"
                                              "Для поиска: /search {РЕСУРС} {НАЗВАНИЕ}\n"
                                              "РЕСУРС = [None(RuTracker), 1337]\n"
                                              "Для скачивания: /download {НОМЕР}\n"
                                              "Для скачивания с сим.: /download\_jl {НОМЕР} {None|НАЗВАНИЕ}\n"
                                              "Для просмотра параметров: /look {НОМЕР}\n\n"
                                              "Для установки кастомного торрент клиента введите: "
                                              "/start {type}:{host}:{port}:{login}:{pass}\n"
                                              "type = [qbittorrent, transmission]\n"
                                              "if host = 'https://', port = 443 \n"
                                         )

    async def user_msg(self, update: Update, context) -> None:
        chat_id = update.effective_chat.id
        client = self.__get_client_by_chat_id(update.effective_chat.id)

        if not client:
            await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                             text="Для начала введите: /start")
            return

        if client.user_states.status == "expecting_name":
            num = client.user_states.num_torrents
            if not num is None:
                text = update.message.text
                if not text.strip():
                    await self.request_name_download(update, context)
                else:
                    await self.handler_cmd_download(update, context, num, text, 'jl')
                    await self.retry_operation(
                        context.bot.delete_message,
                        chat_id=client.chat_id,
                        message_id=client.user_states.bot_msg_id)
                    client.user_states.clear()

        elif client.user_states.status == "search":
            text = update.message.text
            await self.handler_cmd_search(update, context, text, client.tracker_type)
            await self.retry_operation(
                context.bot.delete_message,
                chat_id=client.chat_id,
                message_id=client.user_states.bot_msg_id)
            client.user_states.clear()

        elif client.user_states.status == "setup_tracker":
            text = update.message.text
            if not text in config.TRACKERS:
                print("ошибка выставления трекера")
                return
            client.tracker_type = text
            await self.set_reply_markup(client, update)
            await self.retry_operation(
                context.bot.delete_message,
                chat_id=client.chat_id,
                message_id=client.user_states.bot_msg_id)
            client.user_states.clear()
        elif "🔍 Поиск" in update.message.text and not client.user_states.status:
            client.user_states.status = "search"
            msg = await self.send_message_whit_try(context=context, chat_id=chat_id,
                                                   text="Введите запрос")
            client.user_states.bot_msg_id = msg.message_id
        elif "📦 Трекер:" in update.message.text and not client.user_states.status:
            client.user_states.status = "setup_tracker"
            msg = await self.retry_operation(
                update.message.reply_text,
                reply_markup=self.reply_markup_trackers,
                text="Выберете трекер")
            client.user_states.bot_msg_id = msg.message_id
        else:
            text = update.message.text
            await self.handler_cmd_search(update, context, text, client.tracker_type)
            client.user_states.clear()

        await self.retry_operation(
            context.bot.delete_message,
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id)

    async def cmd_look(self, update: Update, context) -> None:
        try:
            num_ = int(update.message.text.split()[1])
            self.logger.log(f"cmd_look {num_}")
            await self.handler_cmd_look(update, context, num_)
        except Exception as e:
            await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                             text="Поле {НОМЕР} не должно быть пустым")
            self.last_error_st = e
            self.logger.log(f"cmd_look {e}")

    async def handler_cmd_look(self, update: Update, context, num: int) -> None:
        client = self.__get_client_by_chat_id(update.effective_chat.id)
        if not client:
            await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                             text="Для начала введите: /start")
        else:
            try:
                self.logger.log(f"cmd_look {num}")
                if client.get_torrent_info_list_len() < num:
                    await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                     text=f"Номер: {num} отсутствует")
                else:
                    await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                     text=client.get_full_info_torrent(num),
                                                     parse_mode="Markdown")
            except Exception as e:
                await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                 text="Поле {НОМЕР} не должно быть пустым")
                self.last_error_st = e
                self.logger.log(f"h_cmd_look {e}")

    async def cmd_start(self, update: Update, context) -> None:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        msg = await self.send_message_whit_try(context=context, chat_id=chat_id,
                                               text="Регистрация. Ждите")

        client = next((client for client in self.clients if client.user_id == user_id), None)
        if client:
            self.clients.remove(client)

        msg_arg = update.message.text[7:].split(":")
        clients_: BotClient | None = None

        if len(msg_arg) > 3:
            clients_ = BotClient(context, update, msg_arg)
        else:
            if config.ENABLE_WHITE_LIST and (user_id in config.WHITE_LIST):
                clients_ = BotClient(context, update)
            elif msg_arg[0] == config.PASS_TG or not config.ENABLE_PASS_TG:
                clients_ = BotClient(context, update)
            else:
                await self.edit_message_whit_try(context=context, chat_id=chat_id, msg=msg,
                                                 text="Пароль неверный")
        if clients_:
            await self.retry_operation(
                context.bot.delete_message,
                chat_id=update.effective_chat.id,
                message_id=msg.message_id)
            await self.set_reply_markup(clients_, update)
            self.clients.append(clients_)

    async def cmd_last_error(self, update: Update, context) -> None:
        client = self.__get_client_by_chat_id(update.effective_chat.id)
        if not client:
            await self.send_message_whit_try(context=context,
                                             chat_id=update.effective_chat.id,
                                             text="Для начала введите: /start")
        else:
            await self.send_message_whit_try(context=context,
                                             chat_id=update.effective_chat.id,
                                             text=f"{self.last_error_st}")

    async def cmd_log_error(self, update: Update, context) -> None:
        client = self.__get_client_by_chat_id(update.effective_chat.id)
        if not client:
            await self.send_message_whit_try(context=context,
                                             chat_id=update.effective_chat.id,
                                             text="Для начала введите: /start")
        else:
            await self.send_message_whit_try(context=context,
                                             chat_id=update.effective_chat.id,
                                             text=f"{self.logger.get_log_text()}",
                                             disable_web_page_preview=True)

    async def cmd_search(self, update: Update, context) -> None:
        search_arg = update.message.text[8:]
        parts = search_arg.split()
        resource = parts[0] if parts and parts[0] in config.TRACKERS else ""
        await self.handler_cmd_search(update, context, search_arg, resource)

    async def handler_cmd_search(self, update: Update, context,
                                 request: str, tracker_type: str = '') -> None:
        self.num_list_torrent = 0
        self.logger.log(f"cmd_search {request}")
        client = self.__get_client_by_chat_id(update.effective_chat.id)
        if not client:
            await self.send_message_whit_try(context=context,
                                             chat_id=update.effective_chat.id,
                                             text="Для начала введите: /start")
        else:
            if not request:
                await self.send_message_whit_try(context=context,
                                                 chat_id=update.effective_chat.id,
                                                 text="Поле {НАЗВАНИЕ} не должно быть пустым")
            else:
                client.search_torrent(request, tracker_type)
                torrent_info = client.get_torrent_info_part_list(self.num_list_torrent)

                if  not "Не удалось загрузить контент" in torrent_info and client.get_torrent_info_list_len() != 1:
                    if 6 >= client.get_torrent_info_list_len():
                        kye = InlineKeyboardMarkup(self.get_keyboard_list_torrents(False, False, 0,
                                                                                   client.get_torrent_info_list_len()))
                    else:
                        kye = InlineKeyboardMarkup(self.get_keyboard_list_torrents(True, False, 0, 6))

                    await self.send_message_whit_try(context=context,
                                                     chat_id=update.effective_chat.id,
                                                     text=f'''{torrent_info}''',
                                                     reply_markup=kye,
                                                     parse_mode="Markdown",
                                                     disable_web_page_preview=True)
                    return
                await self.send_message_whit_try(context=context,
                                                 chat_id=update.effective_chat.id,
                                                 text=f'''{torrent_info}''',
                                                 parse_mode="Markdown",
                                                 disable_web_page_preview=True)


    async def cmd_download(self, update: Update, context) -> None:
        search_arg = update.message.text[10:].split()
        other = ''

        if search_arg and 'jl' in search_arg:
            other = 'jl'
            search_arg = search_arg[1:]

        num = None
        if isinstance(search_arg[0], int):
            num = int(search_arg[0])

        arg_param = None
        if len(search_arg) > 1:
            arg_param = ' '.join(search_arg[1:])

        self.logger.log(f"cmd_download {search_arg}")
        await self.handler_cmd_download(update, context, num, arg_param, other)

    async def handler_cmd_download(self, update: Update, context,
                                   num: int, name_path: None | str = None, other_param: str | None = None) -> None:
        client = self.__get_client_by_chat_id(update.effective_chat.id)

        if not client:
            await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                             text="Для начала введите: /start")
        else:
            if num is None:
                await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                 text="Поле {НОМЕР} должно содержать цифру")
            else:
                try:
                    if not client.torrent:
                        await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                         text="Ошибка подключения к торрент клиенту")
                    else:
                        if client.get_torrent_info_list_len() < num + 1:
                            await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                             text=f"Номер: {num} отсутствует")
                        else:
                            client.start_download_with_progres_bar(num, update, context, other_param, name_path)
                except Exception as e:
                    self.logger.log(f"Ошибка: {e}")
                    await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                     text="Ошибка обработки команды")
                    self.last_error_st = e
                    self.logger.log(f"h_cmd_download {e}")

    async def retry_operation(self, func, *args, retries=0, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if retries < self.MAX_RETRIES:
                self.logger.log(f"Ошибка сети Telegram: {e}. Попробую снова через 2 секунд. Попытка {retries + 1}/{self.MAX_RETRIES}.")
                if "Can't parse entities:" in str(e):
                    kwargs["parse_mode"] = None
                elif "Message is not modified:" in str(e):
                    return None
                await asyncio.sleep(2)
                return await self.retry_operation(func, *args, retries=retries + 1, **kwargs)
            else:
                self.logger.log(f"Ошибка после {self.MAX_RETRIES} попыток: {e}")
                return None

    async def send_message_whit_try(self, chat_id, text, context, parse_mode=None, reply_markup=None, disable_web_page_preview = False):
        self.logger.log(text)
        return await self.retry_operation(
            context.bot.send_message,
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview
        )

    async def query_update_whit_try(self, text, query, parse_mode=None, reply_markup=None, disable_web_page_preview=False):
        self.logger.log(text)
        return await self.retry_operation(
            query.edit_message_text,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview
        )

    async def set_reply_markup(self, client: BotClient, update: Update):
        reply_markup = self.get_reply_markup(client)
        if client.torrent:
            text = "Готово"
        else:
            text = "Ошибка подключения к торрент клиенту.\nЗагрузка недоступна"

        msg = await self.retry_operation(
            update.message.reply_text,
            reply_markup=reply_markup,
            text=text)

        if client.old_ready_msg_id:
            await self.retry_operation(
                client.context.bot.delete_message,
                chat_id=client.chat_id,
                message_id=client.old_ready_msg_id)
        client.old_ready_msg_id = msg.message_id


    async def edit_message_whit_try(self, chat_id, text, context, msg, parse_mode=None, reply_markup=None):
        self.logger.log(text)
        return await self.retry_operation(
            context.bot.edit_message_text,
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            message_id=msg.message_id
        )

    async def callback_answer_whit_try(self, query):
        return await self.retry_operation(query.answer, show_alert=False)

    async def request_name_download(self, update: Update, context):
        client = self.__get_client_by_chat_id(update.effective_chat.id)
        client.user_states.status = "expecting_name"
        default_name = client.get_default_name_jellyfin()

        if default_name:
            text = f"Введите название для symlink\n(по умолчанию: *{default_name}*)"
            key = InlineKeyboardMarkup([[InlineKeyboardButton("Использовать по умолч.",
                                                              callback_data="used_default_name")]])
            msg = await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                             text=text,
                                             parse_mode="Markdown",
                                             reply_markup=key)
        else:
            text = f"Введите название для symlink"
            msg = await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                             text=text,
                                             parse_mode="Markdown")
        client.user_states.bot_msg_id = msg.message_id

    async def handle_menu_selection(self, update: Update, context):
        query = update.callback_query
        await self.callback_answer_whit_try(query)
        client = self.__get_client_by_chat_id(update.effective_chat.id)
        if not client:
            await self.send_message_whit_try(context=context,
                                             chat_id=update.effective_chat.id,
                                             text="Для начала введите: /start")
            return

        if query.data in ["prev", "next"]:
            if query.data == "prev":
                self.num_list_torrent -= 1
            elif query.data == "next":
                self.num_list_torrent += 1

            if 6 >= client.get_torrent_info_list_len():
                kye = InlineKeyboardMarkup(self.get_keyboard_list_torrents(False, False, 0,
                                                                           client.get_torrent_info_list_len()))
            elif self.num_list_torrent == 0:
                kye = InlineKeyboardMarkup(self.get_keyboard_list_torrents(True, False, 0, 6))
            elif (self.num_list_torrent + 1) * 6 >= client.get_torrent_info_list_len():
                kye = InlineKeyboardMarkup(self.get_keyboard_list_torrents(False, True,
                                                                           self.num_list_torrent * 6,
                                                                           client.get_torrent_info_list_len()))
            else:
                kye = InlineKeyboardMarkup(self.get_keyboard_list_torrents(True, True,
                                                                           self.num_list_torrent * 6,
                                                                           (self.num_list_torrent + 1) * 6))

            torrent_info = client.get_torrent_info_part_list(self.num_list_torrent)
            await self.query_update_whit_try(text=f'{torrent_info}',
                                             reply_markup=kye,
                                             query=query,
                                             parse_mode="Markdown",
                                             disable_web_page_preview=True)

        elif "cancel" in query.data:
            data = query.data.split("_")
            if data[0] == "cancel":
                if int(data[1]) == -1:
                    return
                client.stop_download_torrent(int(data[1]))

        elif "infolook" in query.data:
            data = query.data.split("_")
            await self.handler_cmd_look(update, context, int(data[1]))

        elif "download" in query.data:
            data = query.data.split("_")
            await self.handler_cmd_download(update, context, int(data[1]))

        elif "ljsimlink" in query.data:
            num = int(query.data.split("_")[1])
            client.user_states.num_torrents = num
            await self.request_name_download(update, context)

        elif "used_default_name" in query.data:
            client = self.__get_client_by_chat_id(update.effective_chat.id)
            default_name = client.get_default_name_jellyfin()
            if not client.user_states.num_torrents is None:
                await self.retry_operation(
                    context.bot.delete_message,
                    chat_id=client.chat_id,
                    message_id=client.user_states.bot_msg_id)
                await self.handler_cmd_download(update, context, client.user_states.num_torrents, default_name, 'jl')
            else:
                await self.send_message_whit_try(chat_id=update.effective_chat.id, text="ошибка: used_default_name",
                                                 context=context)
            client.user_states.clear()
        else:
            print("КНОПКИ НЕ СУЩЕСТВУЕТ")


class ProgressBar:
    """
    Класс для создания и обновления прогресс-бара в сообщении Telegram-бота.

    Этот класс создаёт прогресс-бар и обновляет его в сообщении через Telegram API.
    Прогресс-бар обновляется асинхронно с заданным интервалом.
    Атрибуты:
        __progress_value (функция) -> float: Текущее значение прогресса (от 0 до 1).

        __total_step (int): Общее количество шагов для прогресса (по умолчанию 10).

        __chat_id (int): Идентификатор чата пользователя. (update.effective_chat.id)

        __context (ContextTypes.DEFAULT_TYPE): Контекст для взаимодействия с Telegram-API.
    """
    def __init__(self, progress_value, user_id, context, name: str = "", total_step: int = 10, btn = None):
        self.__msg = None
        self.__progress_value = progress_value
        self.__total_step = total_step
        self.__chat_id = user_id
        self.__context = context
        self.__last_message = ""
        self.__name = f'{name[:36]}...\n' if name else ''
        self.btn = btn
        self.state = 1
        self.add_text: str | None = None
        self.logger = SimpleLogger()
        asyncio.create_task(self.__start_progress())

    def __generate_progress_bar(self, progress: float) -> str:
        filled_length = int(self.__total_step * progress)
        bar = "█" * filled_length + "–" * (self.__total_step - filled_length)
        return f"\\[{bar}] {int(progress * 100)}%"

    async def __start_progress(self):
        await self.__progress()

    async def __progress(self):
        progress = 0.
        progress_bar = None
        while progress < 1.:
            progress_bar = self.__generate_progress_bar(progress)
            if self.state == 0:
                self.btn = None
                self.add_text = "\nОстановленно"
                progress_bar = f'{progress_bar}{self.add_text}'

            if progress_bar != self.__last_message:
                self.__last_message = progress_bar
                try:
                    if not self.__msg:
                        self.__msg = await self.__context.bot.send_message(chat_id=self.__chat_id,
                                                                           text=f"{self.__name}Прогресс: {progress_bar}",
                                                                           reply_markup=self.btn,
                                                                           parse_mode="Markdown")
                    else:
                        await self.__context.bot.edit_message_text(chat_id=self.__chat_id, message_id=self.__msg.message_id,
                                                                   text=f"{self.__name}Прогресс: {progress_bar}",
                                                                   reply_markup=self.btn,
                                                                   parse_mode="Markdown")
                    if self.state == 0:
                        break

                except NetworkError as e:
                    self.logger.log(f"Ошибка сети: {e}")
                    print(f"Ошибка сети: {e}")
            await asyncio.sleep(3)
            progress = self.__progress_value()
        try:
            if self.state:
                progress_bar = self.__generate_progress_bar(progress)
                await self.__context.bot.edit_message_text(chat_id=self.__chat_id, message_id=self.__msg.message_id,
                                                text=f"{self.__name}Прогресс: {progress_bar}\nЗагрузка завершена!",
                                                           parse_mode="Markdown")
        except NetworkError as e:
            self.logger.log(f"Ошибка сети: {e}")


class ProgressBarWithBtn(ProgressBar):
    def __init__(self, progress_value, update, context, name: str = "",
                 total_step: int = 10, torrent_id: int | str = None):
        if not torrent_id:
            name = "Ошибка добавления торрента"
            self.__torrent_id = "-1"
            self.btn = self.__generate_buttons()
            progress_value = lambda: 0.
        else:
            self.__torrent_id = torrent_id
            self.btn = self.__generate_buttons()
            self.stop_progress()
        super().__init__(progress_value, update.effective_chat.id, context, name, total_step, self.btn)


    def __generate_buttons(self) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("Отменить", callback_data=f"cancel_{self.__torrent_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def stop_progress(self):
        self.state = 0
