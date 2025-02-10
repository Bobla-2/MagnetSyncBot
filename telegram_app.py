import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
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
import os
from module.logger.logger import SimpleLogger

class BotClient:
    def __init__(self, context: ContextTypes.DEFAULT_TYPE, update: Update, torrent_settings: list = None):
        self.context = context
        self.search_title = ""
        self.chat_id = update.effective_chat.id
        self.user_id = update.effective_user.id

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
        self.__selected_torrent_info: ABCTorrentInfo = None
        self.__dict_progress_bar = {}
        self.__true_name_jellyfin = ''
        self.__creater_link = None
        if config.JELLYFIN_ENABLE:
            self.__creater_link = CreaterSymlinkManager()

    def search_torrent(self, search_title: str) -> None:
        self.__list_torrent_info = self.tracker.get_tracker_list(search_title)
        self.__last_search_title = search_title

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
            items.append(f"{num + (num_ * 6)})    {torrent_info.name}\n")

        add_text, self.__true_name_jellyfin = self.__db_manager.get_info_text_and_names(categories,
                                                                                        self.__last_search_title)
        return f"{''.join(items).replace(']', '').replace('[', '')} {add_text}"

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
                    self.__selected_torrent_info.id_torrent = self.torrent.start_download(
                        self.__selected_torrent_info.get_magnet,
                        subdir)

    def stop_download(self, id_torrent: int) -> None:
        self.torrent.stop_download(id_torrent)
        self.__dict_progress_bar[str(id_torrent)].stop_progress()

    def __start_progresbar(self, update, context, num=None):
        '''
        :param num: default __selected_torrent_info progress
        '''
        torrent_: ABCTorrentInfo = self.__selected_torrent_info if not num else self.__list_torrent_info[num]
        self.__dict_progress_bar[str(torrent_.id_torrent)] = ProgressBarWithBtn(
            progress_value=lambda: self.torrent.get_progress(torrent_.id_torrent),
            update=update,
            context=context,
            total_step=10,
            name=f'{torrent_.name}',
            torrent_id=torrent_.id_torrent)

    def __create_symlink(self, num: int | None = None, arg_param=None) -> None:
        if self.__creater_link:
            torrent_: ABCTorrentInfo = self.__selected_torrent_info if not num else self.__list_torrent_info[num]
            name = self.__true_name_jellyfin
            if arg_param:
                name = arg_param
            self.__creater_link.create_symlink(self.torrent.get_path(torrent_.id_torrent), name,
                                               progress_value=lambda: self.torrent.get_progress(torrent_.id_torrent))

    def start_download_with_progres_bar(self, num, update, context, other, arg_param=None):
        self.__start_download_torrent(num)
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


class TelegramBot:
    MAX_RETRIES = 6
    num_list_torrent = 0

    def __init__(self):
        self.clients: List[BotClient] = []
        self.logger = SimpleLogger()


        self.keyboard_list_next = [
            [InlineKeyboardButton("next   ->", callback_data="next")],
        ]
        self.keyboard_list_prev = [
            [InlineKeyboardButton("<-   prev", callback_data="prev")],
        ]
        self.keyboard_list_next_prev = [[
            InlineKeyboardButton("<-   prev", callback_data="prev"),
            InlineKeyboardButton("next   ->", callback_data="next")

        ]]
        self.keyboard_list_none = []

        self.__add_text_list_torrents = '\nДля скачивания:  /download {НОМЕР}\nДля просмотра:  /look {НОМЕР}'
        if config.JELLYFIN_ENABLE:
            self.__add_text_list_torrents = ('\nДля скачивания:  /download {НОМЕР}'
                                             '\nДля скачивания с сим.: /download\_jl {НОМЕР} {None|НАЗВАНИЕ}'
                                             '\nДля просмотра:  /look {НОМЕР}')

    def setup(self, token):
        self.application = Application.builder().token(token).build()
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("search", self.cmd_search))
        self.application.add_handler(CommandHandler("download", self.cmd_download))
        self.application.add_handler(CommandHandler("download_jl", self.cmd_download))
        self.application.add_handler(CommandHandler("look", self.cmd_look))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.user_msg))
        self.application.add_handler(CallbackQueryHandler(self.handle_menu_selection))


    def run(self):
        self.application.run_polling(timeout=5, poll_interval=1)

    def __get_client_by_chat_id(self, chat_id: int) -> Optional[BotClient]:
        for client in self.clients:
            if client.chat_id == chat_id:
                return client
        return None

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        await self.send_message_whit_try(context=context, chat_id=chat_id,
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

    async def user_msg(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        await self.send_message_whit_try(context=context, chat_id=chat_id,
                                         text="Команда не распознана.\nДля справки введите: /help")

    async def cmd_look(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        client = self.__get_client_by_chat_id(update.effective_chat.id)
        if not client:
            await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                             text="Для начала введите: /start")
        else:
            try:
                num_ = int(update.message.text.split()[1])
                # print(f"cmd_look {num_}")
                self.logger.log(f"cmd_look {num_}")
                if client.get_torrent_info_list_len() < num_:
                    await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                     text=f"Номер: {num_} отсутствует")
                else:
                    await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                     text=client.get_full_info_torrent(num_),
                                                     parse_mode="Markdown")
            except Exception as e:
                await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                 text="Поле {НОМЕР} не должно быть пустым")

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        msg = await self.send_message_whit_try(context=context, chat_id=chat_id,
                                         text="Регистрация. Ждите")

        client = next((client for client in self.clients if client.user_id == user_id), None)
        if client:
            self.clients.remove(client)

        msg_arg = update.message.text[7:].split(":")
        clients_: BotClient = None

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
            if not clients_.torrent:
                await self.edit_message_whit_try(context=context, chat_id=chat_id, msg=msg,
                                                 text="Ошибка подключения к торрент клиенту.\nЗагрузка недоступна\n"
                                                      "Для поиска введите: /search {НАЗВАНИЕ}")
            else:
                await self.edit_message_whit_try(context=context, chat_id=chat_id, msg=msg,
                                             text="Для поиска введите: /search {НАЗВАНИЕ}")
            self.clients.append(clients_)

    async def cmd_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.num_list_torrent = 0
        search_arg = update.message.text[8:]
        # print(f"cmd_search {search_arg}")
        self.logger.log(f"cmd_search {search_arg}")
        client = self.__get_client_by_chat_id(update.effective_chat.id)
        if not client:
            await self.send_message_whit_try(context=context,
                                             chat_id=update.effective_chat.id,
                                             text="Для начала введите: /start")
        else:
            if not search_arg:
                await self.send_message_whit_try(context=context,
                                                 chat_id=update.effective_chat.id,
                                                 text="Поле {НАЗВАНИЕ} не должно быть пустым")
            else:
                client.search_torrent(search_arg)
                torrent_info = client.get_torrent_info_part_list(self.num_list_torrent)
                if 6 >= client.get_torrent_info_list_len():
                    kye = InlineKeyboardMarkup(self.keyboard_list_none)
                else:
                    kye = InlineKeyboardMarkup(self.keyboard_list_next)
                await self.send_message_whit_try(context=context,
                                                 chat_id=update.effective_chat.id,
                                                 text=f'''{torrent_info}{self.__add_text_list_torrents}''',
                                                 reply_markup=kye,
                                                 parse_mode="Markdown",
                                                 disable_web_page_preview=True)

    async def cmd_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        search_arg = update.message.text[10:]
        other = ''
        arg_param = None
        self.logger.log(f"cmd_download {search_arg}")
        client = self.__get_client_by_chat_id(update.effective_chat.id)

        if search_arg[:2] == 'jl':
            other = 'jl'
            search_arg = search_arg.split()[1:]

        if not client:
            await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                             text="Для начала введите: /start")
        else:
            if len(search_arg) < 1:
                await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                 text="Поле {НОМЕР} должно содержать цифру")
            else:
                try:
                    num_ = int(search_arg[0])
                    if not client.torrent:
                        await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                         text="Ошибка подключения к торрент клиенту")
                    else:
                        if client.get_torrent_info_list_len() < num_ + 1:
                            await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                             text=f"Номер: {num_} отсутствует")
                        else:
                            if len(search_arg) > 1:
                                arg_param = ' '.join(search_arg[1:])
                            client.start_download_with_progres_bar(num_, update, context, other, arg_param)
                except Exception as e:
                    self.logger.log(f"Ошибка: {e}")
                    await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                     text="Ошибка обработки команды")

    async def retry_operation(self, func, *args, retries=0, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if retries < self.MAX_RETRIES:
                # print(f"Ошибка сети Telegram: {e}. Попробую снова через 5 секунд. Попытка {retries + 1}/{self.MAX_RETRIES}.")
                self.logger.log(f"Ошибка сети Telegram: {e}. Попробую снова через 5 секунд. Попытка {retries + 1}/{self.MAX_RETRIES}.")
                await asyncio.sleep(2)
                if "Can't parse entities:" in str(e):
                    kwargs["parse_mode"] = None
                return await self.retry_operation(func, *args, retries=retries + 1, **kwargs)
            else:
                # print(f"Ошибка после {self.MAX_RETRIES} попыток: {e}")
                self.logger.log(f"Ошибка после {self.MAX_RETRIES} попыток: {e}")
                return None

    async def send_message_whit_try(self, chat_id, text, context, parse_mode=None, reply_markup=None, disable_web_page_preview = False):
        # print(text)
        self.logger.log(text)
        return await self.retry_operation(
            context.bot.send_message,
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview
        )

    async def query_update_whit_try(self, text, query, parse_mode=None, reply_markup=None, disable_web_page_preview = False):
        # print(text)
        self.logger.log(text)
        return await self.retry_operation(
            query.edit_message_text,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview
        )

    async def edit_message_whit_try(self, chat_id, text, context, msg, parse_mode=None, reply_markup=None):
        # print(text)
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
        return await self.retry_operation(query.answer)

    async def handle_menu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await self.callback_answer_whit_try(query)
        client = self.__get_client_by_chat_id(update.effective_chat.id)
        if query.data in ["prev", "next"]:
            if query.data == "prev":
                self.num_list_torrent -= 1
            elif query.data == "next":
                self.num_list_torrent += 1

            if 6 >= client.get_torrent_info_list_len():
                kye = InlineKeyboardMarkup(self.keyboard_list_none)
            elif self.num_list_torrent == 0:
                kye = InlineKeyboardMarkup(self.keyboard_list_next)
            elif (self.num_list_torrent + 1) * 6 >= client.get_torrent_info_list_len():
                kye = InlineKeyboardMarkup(self.keyboard_list_prev)
            else:
                kye = InlineKeyboardMarkup(self.keyboard_list_next_prev)

            torrent_info = client.get_torrent_info_part_list(self.num_list_torrent)
            await self.query_update_whit_try(text=f'{torrent_info}{self.__add_text_list_torrents}',
                                             reply_markup=kye,
                                             query=query,
                                             parse_mode="Markdown",
                                             disable_web_page_preview=True)

        elif "_" in query.data:
            data = query.data.split("_")
            if data[0] == "cancel":
                client.stop_download(int(data[1]))


class ProgressBar:
    '''
    Класс для создания и обновления прогресс-бара в сообщении Telegram-бота.

    Этот класс создаёт прогресс-бар и обновляет его в сообщении через Telegram API.
    Прогресс-бар обновляется асинхронно с заданным интервалом.
    Атрибуты:
        __progress_value (функция) -> float: Текущее значение прогресса (от 0 до 1).

        __total_step (int): Общее количество шагов для прогресса (по умолчанию 10).

        __chat_id (int): Идентификатор чата пользователя. (update.effective_chat.id)

        __context (ContextTypes.DEFAULT_TYPE): Контекст для взаимодействия с Telegram-API.
    '''
    def __init__(self, progress_value, user_id, context: ContextTypes.DEFAULT_TYPE, name: str = "", total_step: int = 10, btn = None):
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
        return f"[{bar}] {int(progress * 100)}%"

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
                                                                           reply_markup=self.btn)
                    else:
                        await self.__context.bot.edit_message_text(chat_id=self.__chat_id, message_id=self.__msg.message_id,
                                                                   text=f"{self.__name}Прогресс: {progress_bar}",
                                                                   reply_markup=self.btn)
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
                                                text=f"{self.__name}Прогресс: {progress_bar}\nЗагрузка завершена!")
        except NetworkError as e:
            self.logger.log(f"Ошибка сети: {e}")
            # print(f"Ошибка сети: {e}")


class ProgressBarWithBtn(ProgressBar):
    def __init__(self, progress_value, update, context: ContextTypes.DEFAULT_TYPE, name: str = "",
                 total_step: int = 10, torrent_id: int | str = None):
        if not torrent_id:
            name = "Ошибка добавления торрента"
        else:
            self.__torrent_id = torrent_id
            self.btn = self.__generate_buttons()
            self.stop_progress()
        super().__init__(progress_value, update.effective_chat.id, context, name, total_step, self.btn)


    def __generate_buttons(self) -> InlineKeyboardMarkup:
        # Генерация кнопок с уникальным callback_data
        keyboard = [
            [InlineKeyboardButton("Отменить", callback_data=f"cancel_{self.__torrent_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def stop_progress(self):
        self.state = 0

