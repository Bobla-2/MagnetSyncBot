from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import NetworkError
from module.torrent_manager.manager import create_manager
from typing import List, Optional
from module.crypto_token import config
from module.torrent_tracker.main import TorrentTracker
from module.torrent_tracker.TorrentInfoBase import AbstractTorrentInfo
from module.other.jellyfin import CreaterSymlinksJellyfin
import asyncio


class BotClient:
    def __init__(self, context: ContextTypes.DEFAULT_TYPE, update: Update, torrent_settings: list = None):
        self.context = context
        self.search_title = ""
        self.chat_id = update.effective_chat.id
        self.user_id = update.effective_user.id

        self.tracker = TorrentTracker()
        self.x1337 = None
        if torrent_settings:
            self.torrent = create_manager(
                client_type=torrent_settings[0],
                host=torrent_settings[1],
                port=int(torrent_settings[2]),
                username=torrent_settings[3],
                password=torrent_settings[4],
                protocol="https" if torrent_settings[2] == "443" else "http"
                )
        else:
            self.torrent = create_manager(
                client_type=config.tornt_cli_type,
                host=config.tornt_cli_host,
                port=config.tornt_cli_port,
                username=config.tornt_cli_login,
                password=config.get_pass_defualt_torent_client(),
            )

        self.__anime_list: List[AbstractTorrentInfo] = []
        self.__selected_anime: AbstractTorrentInfo = None
        self.__dict_progress_bar = {}
        self.__creater_link = None
        if config.jellyfin:
            self.__creater_link = CreaterSymlinksJellyfin(config.jellyfin_dir)


    def search_anime(self, title: str) -> None:
        self.__anime_list = self.tracker.get_tracker_list(title)

    def get_anime_list(self, num_):
        if not self.__anime_list:
            return "Ничего не найдено"
        return ''.join(f"{num + (num_ * 6)})    {anime.name}\n" for num, anime in enumerate(self.__anime_list[6 * num_:6 * (num_ + 1)]))

    def get_anime_list_len(self) -> int:
        if self.__anime_list:
            return len(self.__anime_list)
        else:
            return 0

    def __start_download_torrent(self, num):
        self.__selected_anime = self.__anime_list[num]
        if self.torrent:
            self.__selected_anime.id_torrent = self.torrent.start_download(self.__selected_anime.get_magnet)

    def stop_download(self, id_torrent: int) -> None:
        self.torrent.stop_download(id_torrent)
        self.__dict_progress_bar[str(id_torrent)].stop_progress()


    def __start_progresbar(self, update, context, num=None):
        '''
        :param num: default __selected_anime progress
        '''
        torrent_: AbstractTorrentInfo = self.__selected_anime if not num else self.__anime_list[num]
        self.__dict_progress_bar[str(torrent_.id_torrent)] = ProgressBarWithBtn(progress_value=lambda: self.torrent.get_progress(torrent_.id_torrent),
                            update=update,
                            context=context,
                            total_step=10,
                            name=f'{torrent_.name}',
                            torrent_id=torrent_.id_torrent)

    def __create_simlink(self, num: int | None = None) -> None:
        if self.__creater_link:
            torrent_: AbstractTorrentInfo = self.__selected_anime if not num else self.__anime_list[num]
            self.__creater_link.create_symlink(torrent_.name, self.torrent.get_path(torrent_.id_torrent))


    def start_download_with_progres_bar(self, num, update, context):
        if self.torrent:
            self.__start_download_torrent(num)
            self.__start_progresbar(update, context)
            self.__create_simlink()


    def get_full_info_torrent(self, num: int) -> str:
        if not self.__anime_list:
            return "Ничего не найдено"
        return self.__anime_list[num].full_info


class TelegramBot:
    MAX_RETRIES = 6
    num_list_torrent = 0

    def __init__(self, token):
        self.clients: List[BotClient] = []
        self.application = Application.builder().token(token).build()
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("search", self.cmd_search))
        self.application.add_handler(CommandHandler("download", self.cmd_download))
        self.application.add_handler(CommandHandler("look", self.cmd_look))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.user_msg))
        self.application.add_handler(CallbackQueryHandler(self.handle_menu_selection))

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

    def run(self):
        self.application.run_polling()

    def __get_client_by_chat_id(self, chat_id: int) -> Optional[BotClient]:
        for client in self.clients:
            if client.chat_id == chat_id:
                return client
        return None

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        await self.send_message_whit_try(context=context, chat_id=chat_id,
                                         text="Для начала введите: /start\n"
                                              "Для поиска: /search {РЕСУРС} {НАЗВАНИЕ}\n"
                                              "РЕСУРС = [None(RuTracker), 1337]\n"
                                              "Для скачивания: /download {НОМЕР}\n"
                                              "Для просмотра параметров: /look {НОМЕР}\n\n"
                                              "Для установки кастомного торрент клиента введите: "
                                              "/start {type}:{host}:{port}:{login}:{pass}\n"
                                              "type = [qbittorrent, transmission]\n"
                                              "if host = 'https://', port = 443 \n"
                                              )

    async def user_msg(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        await self.send_message_whit_try(context=context, chat_id=chat_id, text="Для справки введите: /help")

    async def cmd_look(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        client = self.__get_client_by_chat_id(update.effective_chat.id)
        if not client:
            await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                             text="Для начала введите: /start")
        else:
            try:
                num_ = int(update.message.text.split()[1])
                print(str(num_))
                if client.get_anime_list_len() < num_:
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
        if len(msg_arg) > 2:
            self.clients.append(BotClient(context, update, msg_arg))
        else:
            self.clients.append(BotClient(context, update))
        if not self.clients[-1].torrent:
            await self.edit_message_whit_try(context=context, chat_id=chat_id, msg=msg,
                                             text="Ошибка подключения к торрент клиенту.\nЗагрузка недоступна\n"
                                                  "Для поиска введите: /search {НАЗВАНИЕ}")
        else:
            await self.edit_message_whit_try(context=context, chat_id=chat_id, msg=msg,
                                             text="Для поиска введите: /search {НАЗВАНИЕ}")

    async def cmd_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.num_list_torrent = 0
        search_arg = update.message.text[8:]
        print(f"cmd_search {search_arg}")
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
                client.search_anime(search_arg)
                anime = client.get_anime_list(self.num_list_torrent)
                if 6 >= client.get_anime_list_len():
                    kye = InlineKeyboardMarkup(self.keyboard_list_none)
                else:
                    kye = InlineKeyboardMarkup(self.keyboard_list_next)
                await self.send_message_whit_try(context=context,
                                                 chat_id=update.effective_chat.id,
                                                 text=f'''{anime}\n\nДля скачивания:  /download {{НОМЕР}}\nДля просмотра параметров:  /look {{НОМЕР}}''',
                                                 reply_markup=kye)

    async def cmd_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        search_arg = update.message.text[10:]
        print(search_arg)
        client = self.__get_client_by_chat_id(update.effective_chat.id)
        if not client:
            await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                             text="Для начала введите: /start")
        else:
            if not search_arg:
                await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                 text="Поле {НОМЕР} должно содержать цифру")
            else:
                try:
                    search_arg = int(search_arg)
                    if not client.torrent:
                        await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                         text="Ошибка подключения к торрент клиенту")
                    else:
                        if client.get_anime_list_len() < search_arg:
                            await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                             text=f"Номер: {search_arg} отсутствует")
                        else:
                            client.start_download_with_progres_bar(search_arg, update, context)
                except:
                    await self.send_message_whit_try(context=context, chat_id=update.effective_chat.id,
                                                     text="Поле {НОМЕР} должно содержать цифру")

    async def retry_operation(self, func, *args, retries=0, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if retries < self.MAX_RETRIES:
                print(f"Ошибка сети Telegram: {e}. Попробую снова через 5 секунд. Попытка {retries + 1}/{self.MAX_RETRIES}.")
                await asyncio.sleep(2)
                if "Can't parse entities:" in str(e):
                    kwargs["parse_mode"] = None
                return await self.retry_operation(func, *args, retries=retries + 1, **kwargs)
            else:
                print(f"Ошибка после {self.MAX_RETRIES} попыток: {e}")
                return None

    async def send_message_whit_try(self, chat_id, text, context, parse_mode=None, reply_markup=None):
        print(text)
        return await self.retry_operation(
            context.bot.send_message,
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )

    async def query_update_whit_try(self, text, query, parse_mode=None, reply_markup=None):
        print(text)
        return await self.retry_operation(
            query.edit_message_text,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )

    async def edit_message_whit_try(self, chat_id, text, context, msg, parse_mode=None, reply_markup=None):
        print(text)
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

            if 6 >= client.get_anime_list_len():
                kye = InlineKeyboardMarkup(self.keyboard_list_none)
            elif self.num_list_torrent == 0:
                kye = InlineKeyboardMarkup(self.keyboard_list_next)
            elif (self.num_list_torrent + 1) * 6 >= client.get_anime_list_len():
                kye = InlineKeyboardMarkup(self.keyboard_list_prev)
            else:
                kye = InlineKeyboardMarkup(self.keyboard_list_next_prev)

            anime = client.get_anime_list(self.num_list_torrent)
            await self.query_update_whit_try(text=f'{anime}\n\nДля скачивания:  /download {{НОМЕР}}\nДля просмотра параметров:  /look {{НОМЕР}}',
                                             reply_markup=kye,
                                             query=query)

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
        self.add_text: str = None
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
                        # self.state = 1

                except NetworkError as e:
                    print(f"Ошибка сети: {e}")
            await asyncio.sleep(3)
            progress = self.__progress_value()
        try:
            if self.state:
                progress_bar = self.__generate_progress_bar(progress)
                await self.__context.bot.edit_message_text(chat_id=self.__chat_id, message_id=self.__msg.message_id,
                                                text=f"{self.__name}Прогресс: {progress_bar}\nЗагрузка завершена!")
        except NetworkError as e:
            print(f"Ошибка сети: {e}")


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

