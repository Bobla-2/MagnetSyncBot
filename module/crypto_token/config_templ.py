import os

######################### - UI - #########################
UI_MODE = "web"   # web / tg

######################### - proxy - #########################
proxy = 'http://127.0.0.1:10808'

X1337_BASE_URL = 'https://1337x.to'
ANILIBRIA_BASE_URL = 'https://aniliberty.top'
ANIDUB_BASE_URL = 'https://tr.anidub.com'
RUTRACKER_FORUM_URL = 'https://rutracker.org/forum'
NMCLUB_BASE_URL = "https://nnmclub.to"
BD_PATH = os.getenv("BD_PATH", "./torrents.bd")
TRACKERS = ["Rutracker", "NnmClub", "AniDub", "Anilibria", "Local"] # "1337x"
######################### - torrent client default - #########################
tornt_cli_host = "127.0.0.1"
tornt_cli_port = 9091
tornt_cli_type = "transmission"  # можно transmission/qbittorrent
tornt_cli_login = "transmission"
tornt_cli_pass = "transmission"

TORRENT_FOLDER_OTHER = "/downloads/1_other"       # абсолютный путь, в куда качаются торренты
TORRENT_FOLDER_SOFT = "/downloads/1_soft"
TORRENT_FOLDER_GAME = "/downloads/1_game"
TORRENT_FOLDER_CINEMA = "/downloads/1_cinema"
TORRENT_FOLDER_ANIME = "/downloads/1_anime"
TORRENT_FOLDER_MUSIC = "/downloads/1_music"

######################### - telegram - #########################
tg_token = "xxxxxxxxxxx"

# пароль для входа с настройками по умолчанию (/start {pass})
ENABLE_PASS_TG = True
PASS_TG = "1234567"

# пользовотелей из WHITE_LIST пускает без пароля
ENABLE_WHITE_LIST = True
WHITE_LIST = []       # id telegram
######################### - rutecker - #########################
RUTRACKER_LOGIN = "login"
RUTRACKER_PASS = "pass"
######################### - poiskkino - #########################
ENABLE_KINOPOISK = True
KINOPOISK_BASE_URL = "https://api.poiskkino.dev/v1.4/movie/search"
API_TOKEN_KINOPOISK = 'xxxxxxxx'

######################### - jellyfin - #########################
JELLYFIN_ENABLE = True    # создание симлинков для jellyfin не работает

JELLYFIN_FOLDER_OTHER = "/DLNA/1_other"
JELLYFIN_FOLDER_SOFT = "/DLNA/1_soft"
JELLYFIN_FOLDER_GAME = "/DLNA/1_game"
JELLYFIN_FOLDER_CINEMA = "/DLNA/1_cinema"
JELLYFIN_FOLDER_ANIME = "/DLNA/1_anime"
JELLYFIN_FOLDER_MUSIC = "/DLNA/1_music"

SYMLINK_IS_SSH = True     # так как бот в докере, лучше использовать всегда ssh
SYMLINK_HOST = tornt_cli_host
SYMLINK_PORT = 22
SYMLINK_LOGIN = 'login'
SYMLINK_PASS = 'pass'

########################## Дальше только настройки сортировки #######################################
################################################################################
################################################################################
################################################################################


# настройки сортировщика
# он должен состоять из [[список категорий], относительный путь куда симлинк, тип сортировки]
# тип сортировки может быть: "==" -> категория должна совпадать; "in" -> категория должна содержать ключевое слово
# СОРТИРОВЩИК ПЕРЕЕХАЛ В САМЫЙ НИЗ



################################################################################
################################################################################
################################################################################




categories_cinema_rutr = [
    "UHD Video",
    "Видео",
    "Кино СССР",
    "Детские отечественные фильмы",
    "Авторские дебюты",
    "Фильмы России и СССР на национальных языках [без перевода]",
    "Классика мирового кинематографа",
    "Фильмы до 1990 года",
    "Фильмы 1991-2000",
    "Фильмы 2001-2005",
    "Фильмы 2006-2010",
    "Фильмы 2011-2015",
    "Фильмы 2016-2020",
    "Фильмы 2021-2024",
    "Фильмы 2021-2025",
    "Фильмы 2025",
    "Фильмы ближнего зарубежья",
    "Азиатские фильмы",
    "Индийское кино",
    "Сборники фильмов",
    "Короткий метр",
    "Грайндхаус",
    "Зарубежные фильмы без перевода",
    "Звуковые дорожки и Переводы",
    "Короткий метр (Арт-хаус и авторское кино)",
    "Документальные фильмы (Арт-хаус и авторское кино)",
    "Анимация (Арт-хаус и авторское кино)",
    "Спектакли без перевода",
    "Классика мирового кинематографа (DVD Video)",
    "Зарубежное кино (DVD Video)",
    "Наше кино (DVD Video)",
    "Фильмы Ближнего Зарубежья (DVD Video)",
    "Азиатские фильмы (DVD Video)",
    "Арт-хаус и авторское кино (DVD Video)",
    "Индийское кино (DVD Video)",
    "Грайндхаус (DVD Video)",
    "Классика мирового кинематографа (HD Video)",
    "Зарубежное кино (HD Video)",
    "Наше кино (HD Video)",
    "Фильмы Ближнего Зарубежья (HD Video)",
    "Азиатские фильмы (HD Video)",
    "Арт-хаус и авторское кино (HD Video)",
    "Индийское кино (HD Video)",
    "Грайндхаус (HD Video)",
    "Классика мирового кинематографа (UHD Video)",
    "Зарубежное кино (UHD Video)",
    "Наше кино (UHD Video)",
    "Наше кино",
    "Азиатские фильмы (UHD Video)",
    "Арт-хаус и авторское кино (UHD Video)",
    "3D Кинофильмы",
    "3D Мультфильмы",
    "3D Документальные фильмы",
    "3D Спорт",
    "3D Ролики, Музыкальное видео, Трейлеры к фильмам",
    "Мультфильмы (UHD Video)",
    "Отечественные мультфильмы (HD Video)",
    "Иностранные мультфильмы (HD Video)",
    "Иностранные короткометражные мультфильмы (HD Video)",
    "Отечественные мультфильмы (DVD)",
    "Иностранные короткометражные мультфильмы (DVD)",
    "Иностранные мультфильмы (DVD)",
    "Отечественные мультфильмы",
    "Отечественные полнометражные мультфильмы",
    "Мультфильмы Ближнего Зарубежья",
    "Иностранные мультфильмы",
    "Иностранные короткометражные мультфильмы",
    "Сборники мультфильмов",
    "Мультфильмы без перевода",
    "Мультсериалы (SD Video)",
    "Мультсериалы (DVD Video)",
    "Мультсериалы (HD Video)",
    "Мультсериалы (UHD Video)"
]

categories_game_rutr = [
    "Игры для Windows",
    "Горячие Новинки",
    "Аркады",
    "Файтинги",
    "Экшены от первого лица",
    "Экшены от третьего лица",
    "Хорроры",
    "Приключения и квесты",
    "Квесты в стиле \"Поиск предметов\"",
    "Визуальные новеллы",
    "Для самых маленьких",
    "Логические игры",
    "Шахматы",
    "Ролевые игры",
    "Симуляторы",
    "Стратегии в реальном времени",
    "Пошаговые стратегии",
    "Антологии и сборники игр",
    "Старые игры (Экшены)",
    "Старые игры (Ролевые игры)",
    "Старые игры (Стратегии)",
    "Старые игры (Приключения и квесты)",
    "Старые игры (Симуляторы)",
    "IBM-PC-несовместимые компьютеры",
    "Прочее для Windows-игр",
    "Официальные патчи, моды, плагины, дополнения",
    "Неофициальные модификации, плагины, дополнения",
    "Русификаторы",
    "Прочее для Microsoft Flight Simulator, Prepar3D, X-Plane",
    "Сценарии, меши и аэропорты для FS2004, FSX, P3D",
    "Самолёты и вертолёты для FS2004, FSX, P3D",
    "Миссии, трафик, звуки, паки и утилиты для FS2004, FSX, P3D",
    "Сценарии, миссии, трафик, звуки, паки и утилиты для X-Plane",
    "Самолёты и вертолёты для X-Plane",
    "Игры для Apple Macintosh",
    "Нативные игры для Mac",
    "Игры для Mac с Wineskin, DOSBox, Cider и другими",
    "Игры для Linux",
    "Нативные игры для Linux",
    "Игры для Linux с Wine, DOSBox и другими",
    "Игры для консолей",
    "PS",
    "PS2",
    "PS3",
    "PS4",
    "PS5",
    "PSP",
    "Игры PS1 для PSP",
    "PS Vita",
    "Original Xbox",
    "Xbox 360",
    "Wii/WiiU",
    "NDS/3DS",
    "Switch",
    "Dreamcast",
    "Остальные платформы",
    "Видео для консолей",
    "Видео для PS Vita",
    "Фильмы для PSP",
    "Сериалы для PSP",
    "Мультфильмы для PSP",
    "Дорамы для PSP",
    "Аниме для PSP",
    "Видео для PSP",
    "Видео для PS3 и других консолей",
    "Игры для мобильных устройств",
    "Игры для Android",
    "Игры для Oculus Quest",
    "Игры для Symbian",
    "Игры для Windows Mobile",
    "Игровое видео",
    "Видеопрохождения игр"
]

categories_soft_rutr = [
    "Операционные системы от Microsoft",
    "Оригинальные образы Windows",
    "Сборки Windows 8 и далее",
    "Сборки Windows XP - Windows 7",
    "Операционные системы выпущенные до Windows XP",
    "Серверные ОС (оригинальные + сборки)",
    "Разное (сборки All-in-One, пакеты обновлений, утилиты, и прочее)",
    "Linux, Unix и другие ОС",
    "Операционные системы (Linux, Unix)",
    "Программное обеспечение (Linux, Unix)",
    "Другие ОС и ПО под них",
    "Системные программы",
    "Работа с жёстким диском",
    "Резервное копирование",
    "Архиваторы и файловые менеджеры",
    "Программы для настройки и оптимизации ОС",
    "Сервисное обслуживание компьютера",
    "Работа с носителями информации",
    "Информация и диагностика",
    "Программы для интернет и сетей",
    "ПО для защиты компьютера (Антивирусное ПО, Фаерволлы)",
    "Драйверы и прошивки",
    "Оригинальные диски к компьютерам и комплектующим",
    "Серверное ПО для Windows",
    "Изменение интерфейса ОС Windows",
    "Скринсейверы",
    "Разное (Системные программы под Windows)",
    "Системы для бизнеса, офиса, научной и проектной работы",
    "Медицина - интерактивный софт",
    "Всё для дома: кройка, шитьё, кулинария",
    "Офисные системы",
    "Системы для бизнеса",
    "Распознавание текста, звука и синтез речи",
    "Работа с PDF и DjVu",
    "Словари, переводчики",
    "Системы для научной работы",
    "САПР (общие и машиностроительные)",
    "САПР (электроника, автоматика, ГАП)",
    "Программы для архитекторов и строителей",
    "Библиотеки и проекты для архитекторов и дизайнеров интерьеров",
    "Прочие справочные системы",
    "Разное (Системы для бизнеса, офиса, научной и проектной работы)",
    "WYSIWYG Редакторы для веб-диза",
    "Текстовые редакторы с подсветкой",
    "Среды программирования, компиляторы и вспомогательные программы",
    "Компоненты для сред программирования",
    "Системы управления базами данных",
    "Скрипты и движки сайтов, CMS а также расширения к ним",
    "Шаблоны для сайтов и CMS",
    "Разное (Веб-разработка и программирование)",
    "Тестовые диски для настройки аудио/видео аппаратуры",
    "Программные комплекты",
    "Плагины для программ компании Adobe",
    "Графические редакторы",
    "Программы для верстки, печати и работы со шрифтами",
    "3D моделирование, рендеринг и плагины для них",
    "Анимация",
    "Создание BD/HD/DVD-видео",
    "Редакторы видео",
    "Видео- Аудио- конверторы",
    "Аудио- и видео-, CD- проигрыватели и каталогизаторы",
    "Каталогизаторы и просмотрщики графики",
    "Разное (Программы для работы с мультимедиа и 3D)",
    "Виртуальные студии, секвенсоры и аудиоредакторы",
    "Виртуальные инструменты и синтезаторы",
    "Плагины для обработки звука",
    "Разное (Программы для работы со звуком)",
    "Авторские работы",
    "Официальные сборники векторных клипартов",
    "Прочие векторные клипарты",
    "Photostocks",
    "Дополнения для программ компоузинга и постобработки",
    "Рамки, шаблоны, текстуры и фоны",
    "Прочие растровые клипарты",
    "3D модели, сцены и материалы",
    "Футажи",
    "Прочие сборники футажей",
    "Музыкальные библиотеки",
    "Звуковые эффекты",
    "Библиотеки сэмплов",
    "Библиотеки и саундбанки для сэмплеров, пресеты для синтезаторов",
    "Multitracks",
    "Материалы для создания меню и обложек DVD",
    "Дополнения, стили, кисти, формы, узоры для программ Adobe",
    "Шрифты",
    "Разное (Материалы для мультимедиа и дизайна)",
    "ГИС, системы навигации и карты",
    "ГИС (Геоинформационные системы)",
    "Карты, снабженные программной оболочкой",
    "Атласы и карты современные (после 1950 г.)",
    "Атласы и карты старинные (до 1950 г.)",
    "Карты прочие (астрономические, исторические, тематические)",
    "Встроенная автомобильная навигация",
    "Garmin",
    "Ozi",
    "TomTom",
    "Navigon / Navitel",
    "Igo",
    "Разное - системы навигации и карты",
    "Приложения для мобильных устройств",
    "Приложения для Android",
    "Приложения для Java",
    "Приложения для Symbian",
    "Приложения для Windows Mobile",
    "Софт для работы с телефоном",
    "Прошивки для телефонов",
    "Обои и темы",
    "Видео для мобильных устройств",
    "Видео для смартфонов и КПК",
    "Видео в формате 3GP для мобильных",
    "Apple Macintosh",
    "Mac OS (для Macintosh)",
    "Mac OS (для РС-Хакинтош)",
    "Программы для просмотра и обработки видео (Mac OS)",
    "Программы для создания и обработки графики (Mac OS)",
    "Плагины для программ компании Adobe (Mac OS)"
]

categories_anime_rutr = ['Аниме (HD Video)', 'Аниме (SD Video)', 'Аниме (DVD Video)', 'Аниме (QC подраздел)', 'Аниме (плеерный подраздел)', 'Японские мультфильмы', 'Дунхуа и Эни', 'Онгоинги (HD Video)', 'Ван-Пис', 'Гандам', 'Наруто', 'Покемоны', 'Архив (Аниме)']

categories_soft_nnmclub = [
    "ОС Windows",
    "Оригинальные версии Windows",
    "Оригинальные версии Windows Server",
    "Windows OEM Recovery CD/DVD",
    "Сборки Windows 11",
    "Сборки Windows 10",
    "Сборки Windows 8",
    "Сборки Windows 7",
    "Сборки Windows Vista",
    "Сборки Windows XP",
    "Сборки Windows - всё в одном",
    "Сборки Windows для незрячих",
    "Песочница ПО и сборок Windows",
    "Разное (RC, Beta и Service Packs)",
    "Музей Windows",
    "Утилиты, Офис, Интернет",
    "ПО для Интернета и сетей",
    "Оригинальные версии Office",
    "Офисное ПО",
    "Запись, создание, редактирование, эмуляция дисков и...",
    "Диагностика и обслуживание hardware",
    "Резервирование и восстановление данных",
    "Файловые менеджеры и архиваторы",
    "Обслуживание ОС",
    "Разное (Утилиты, Офис, Интернет)",
    "Безопасность",
    "Firewalls",
    "Антивирусы",
    "Комплексные системы защиты",
    "Разное (остальные программы по безопасности)",
    "Мультимедиа и Графика",
    "Аудио Плееры и Кодеки",
    "Аудио Граббинг, Мастеринг, Обработка",
    "Прочее ПО для Аудио",
    "Видео Плееры и Кодеки",
    "Нелинейный Видеомонтаж, Авторинг, Кодировщики",
    "Просмотрщики Графики (вьюверы)",
    "Графические редакторы",
    "ПО для моделирования",
    "LiveCD/DVD/Flash",
    "WPI",
    "Серверное ПО",
    "Разработка ПО",
    "САПР/ГИС",
    "Системы навигации и карты",
    "Драйверы",
    "macOS (Apple)",
    "macOS (osx86project/hackintosh)",
    "Разное для macOS (Apple/hackintosh)",

    "Графика для macOS",
    "CAD, 3D, ПО для специалистов для macOS",
    "Офис, Интернет для macOS",
    "Аудио и видео редакторы для macOS",
    "Плееры, конвертеры, кодеки для macOS",
    "Утилиты для macOS",

    "Прошивки iOS и AppleTV",
    "UnLock, Jailbreak, Cydia",
    "ПО для iOS",
    "ПО из App Store",

    "Отечественное видео для устройств Apple",
    "Отечественное видео HD для устройств Apple",
    "Зарубежное видео для устройств Apple",
    "Зарубежное видео HD для устройств Apple",
]

categories_game_nnmclub = [
    "Визуальные новеллы",
    "Win Игры",
    "Горячие новинки Игр",
    "Песочница Win Игр",

    "Action (FPS)",
    "Action (TPS)",
    "Adventure/Quest",
    "Arcade",
    "RPG",
    "Online (MMO)",
    "Online Action (MMO)",

    "Strategy (RTS/TBS/Grand)",
    "Strategy Tactical (RTS/TBS)",
    "Strategy (Manage/Busin)",

    "Racing",
    "Simulation (Flight/Space)",
    "Simulation (Sport)",
    "Simulation (Other)",

    "Action/Arcade/Platformer (Casual)",
    "Adventure/Quest (Casual)",
    "Classic Arcade/Zuma/3match (Casual)",
    "Board/Puzzle/Logic (Casual)",
    "Strategy/Manager/Business (Casual)",

    "AddOn/DLC/Mod для Игр",
    "Demo/Beta версии Игр",
    "Языковые пакеты для Игр",
    "Patch/Tweak/Trainer/Other для Игр",
    "NoCD/NoDVD/Crack для Игр",

    "Win Старые Игры",

    "Консольные Игры",
    "Тех. раздел Консолей",

    "Xbox 360",
    "Wii, GameCube",
    "Wii U",
    "Switch",

    "PS1",
    "PS2",
    "PS3",
    "PS4",
    "PSP",
    "PS Vita",
    "Psx to PSP",

    "Ромы",
    "Другие приставки",
    "Kinder Games для macOS",
    "Quests, Adventure, Arcade для macOS",
    "Action, FPS для macOS",
    "Strategy, RPG для macOS",
    "Racing, Simulation, Sports для macOS",
    "Casual Games, Other для macOS",
    "Тестовые macOS Игры",

    "Игры для iOS",
]

categories_cinema_nnmclub = [
    "hand made * video",

    "Горячие новинки",
    "Отечественные Новинки (SD, DVD)",
    "Зарубежные Новинки (SD, DVD)",
    "Отечественные Новинки (HD, FHD, UHD, 3D)",
    "Зарубежные Новинки (HD, FHD, UHD, 3D)",
    "Экранки",
    "Экранки с рекламой",
    "Новинки с Рекламой",

    "Классика кино и Старые фильмы до 90-х",
    "Отечественная Классика (SD)",
    "Отечественная Классика (DVD)",
    "Отечественная Классика (HD, FHD, UHD)",
    "Зарубежная Классика (SD)",
    "Зарубежная Классика (DVD)",
    "Зарубежная Классика (HD, FHD, UHD, 3D)",

    "Старые Отечественные Фильмы (SD)",
    "Старые Отечественные Фильмы (DVD)",
    "Старые Отечественные Фильмы (HD, FHD, UHD)",
    "Старые Зарубежные Фильмы (SD)",
    "Старые Зарубежные Фильмы (DVD)",
    "Старые Зарубежные Фильмы (HD, FHD, UHD, 3D)",

    "Отечественное кино",
    "Отечественные Фильмы (SD)",
    "Отечественные Фильмы (DVD)",
    "Отечественные Фильмы (HD, FHD, UHD)",
    "Отечественные Фильмы (3D)",

    "Зарубежное кино",
    "Зарубежные Фильмы (SD)",
    "Зарубежные Фильмы (DVD)",
    "Зарубежные Фильмы (HD, FHD)",
    "Зарубежные Фильмы (UHD)",
    "Зарубежные Фильмы (3D)",

    "Азиатское кино",
    "Азиатское кино (SD)",
    "Азиатское кино (DVD)",
    "Азиатское кино (HD, FHD, UHD)",
    "Азиатское кино (3D)",

    "Индийское кино",

    "Фильмы в оригинале",
    "Фильмы в оригинале (SD, DVD)",
    "Фильмы в оригинале (HD, FHD, UHD)",

    "Коллекции / *логии",
    "Зарубежное кино (коллекции / *логии)",
    "Отечественное кино (коллекции / *логии)",

    "Музыкальные клипы",
    "Концерты",
    "Концерты (SD)",
    "Концерты (DVD)",
    "Концерты (HD, FHD, UHD, 3D)",

    "Театр",
    "Опера, Балет, Мюзиклы",
    "Караоке",

    "Игровое видео",
    "Трейлеры",
    "Звуковые дорожки и субтитры",

    "Фильмы с Рекламой",

    "Классика сериалов и многосерийное кино до 90-х",
    "Отечественная классика сериалов и старое многосерийное кино",
    "Зарубежная классика сериалов и старое многосерийное кино",

    "Зарубежные сериалы",

    "Чертова служба в госпитале МЭШ / M*A*S*H",
    "Звездные войны / Star Wars (сериалы по франшизе)",
    "Анатомия страсти / Grey's Anatomy",
    "Во все тяжкие / Breaking Bad; Лучше звоните Солу / Better Call Saul",
    "Грань / Fringe",
    "Дневники вампира / Vampire Diaries; Настоящая кровь",
    "Доктор кто / Doctor Who; Торчвуд / Torchwood",
    "Доктор Хаус / House M.D.",
    "Звездные врата / Stargate",
    "Звездный Крейсер Галактика / Battlestar Galactica",
    "Звездный путь / Star Trek; Орвилл / The Orville",
    "Игра престолов / Game of Thrones",
    "Касл / Castle",
    "Кости / Bones",
    "Менталист / The Mentalist; Теория Лжи / Lie To Me",
    "Место преступления / CSI",
    "Морская полиция / NCIS; Военно-юридическая служба",
    "Побег / Prison Break",
    "Пуаро / Poirot",
    "Сверхъестественное / Supernatural",
    "Секретные материалы / The X-Files",
    "Теория Большого Взрыва / The Big Bang Theory; Детство Шелдона",
    "Ходячие мертвецы / The Walking Dead; Бойтесь ходячих мертвецов",

    "Сериалы ближнего зарубежья",
    "Сериалы DC Comics",
    "Сериалы Marvel Comics",

    "Азиатские сериалы",
    "Латиноамериканские сериалы",
    "Турецкие сериалы",

    "Сериалы без русского перевода (украинская озвучка)",
    "Сериалы без перевода",
    "Сериалы с рекламой",

    "Отечественные сериалы",

    "Бандитский Петербург",
    "Глухарь",
    "Интерны",
    "Ментовские войны",
    "Менты",
    "Солдаты",
    "Универ",
]

categories_anime_nnmclub = [
    "Аниме арт",
    "Аниме с субтитрами",
    "Онгоинги",
    "Аниме (SD)",
    "Аниме (HD)",
    "Аниме (FullHD)",
    "Аниме с озвучкой",
    "Онгоинги с озвучкой",
    "Аниме с озвучкой (SD)",
    "Аниме с озвучкой (HD)",
    "Аниме с озвучкой (FullHD)",
    "Аниме разное",
    "Аниме DVD",
    "Аниме Blu-ray, Remux",
    "Аниме хардсаб",
    "Аниме прочее",
]

categories_music_nnmclub = [
    "Музыка (AAC)",
    "Музыка Lossless (ALAC)",
    "Аудиокниги (AAC)",
    "Аниме музыка",
    "Аниме OST (Lossless)",
    "Аниме OST",

    "HD Audio и Многоканальная Музыка",
    "Blu-ray Audio",
    "DVD-Audio",
    "SACD-R",
    "DTS-Audio",
    "Vinyl-Rip и Hand-Made",

    "Классика",
    "Классика (Hi-Res)",
    "Классика (сборники)",
    "Полные собрания сочинений",
    "Полные собрания сочинений (Lossless)",
    "Вокал",
    "Вокал (Lossless)",
    "Концерты",
    "Концерты (Lossless)",
    "Оркестровая",
    "Оркестровая (Lossless)",
    "Камерная",
    "Камерная (Lossless)",
    "Фортепиано",
    "Фортепиано (Lossless)",
    "Classical Crossover / Neoclassical",
    "Classical Crossover / Neoclassical (Lossless)",

    "Jazz",
    "Jazz (Hi-Res)",
    "Jazz (Lossless)",
    "Blues, Soul",
    "Blues, Soul (Hi-Res)",
    "Blues, Soul (Lossless)",

    "Шансон, Авторская и Военная песня",
    "Шансон, Авторская и Военная песня (Hi-Res)",
    "Русский Шансон",
    "Русский Шансон (Lossless)",
    "Зарубежный Шансон",
    "Зарубежный Шансон (Lossless)",
    "Авторская и Военная песня",
    "Авторская и Военная песня (Lossless)",

    "Rock",
    "Rock (Hi-Res)",
    "Rock (Lossless)",
    "Alternative, Punk",
    "Alternative, Punk (Hi-Res)",
    "Alternative, Punk (Lossless)",
    "Hard Rock",
    "Hard Rock (Hi-Res)",
    "Hard Rock (Lossless)",
    "Metal",
    "Metal (Hi-Res)",
    "Metal (Lossless)",
    "Русский рок",
    "Русский Рок (Hi-Res)",
    "Русский Рок (Lossless)",

    "Pop",
    "Pop (Hi-Res)",
    "Eurodance, Disco",
    "Eurodance, Euro-House, Technopop",
    "Eurodance, Euro-House, Technopop (Lossless)",
    "Disco, Italo-Disco, Euro-Disco, Hi-NRG",
    "Disco, Italo-Disco, Euro-Disco, Hi-NRG (Lossless)",
    "Отечественная поп-музыка",
    "Отечественная поп-музыка (Lossless)",
    "Советская эстрада, Ретро",
    "Советская эстрада, Ретро (Lossless)",
    "Зарубежная поп-музыка",
    "Зарубежная поп-музыка (Lossless)",

    "Electronic",
    "Psybient, Psychill, Psydub",
    "Psybient, Psychill, Psydub (Lossless)",
    "Downtempo, Trip-Hop, Lounge",
    "Downtempo, Trip-Hop, Lounge (Lossless)",
    "Downtempo, Ambient (Hi-Res)",
    "Ambient, Experimental, Modern Classical",
    "Ambient, Experimental, Modern Classical (Lossless)",
    "Experimental, Industrial (Hi-Res)",

    "Trance",
    "Trance (Lossless)",
    "House",
    "Techno, Electro, Minimal",
    "House, Techno, Electro, Minimal (Lossless)",
    "Trance, House, Techno (Hi-Res)",

    "Drum'n'Bass, Jungle, Breaks, Breakbeat",
    "Drum'n'Bass, Jungle, Breaks, Breakbeat (Lossless)",
    "Drum'n'Bass, Breakbeat (Hi-Res)",

    "Dubstep, Future Garage, Bass Music, UK Garage",
    "Dubstep, Future Garage, Bass Music, UK Garage (Lossless)",

    "Hardstyle, Jumpstyle, Hardcore",
    "Hardstyle, Jumpstyle, Hardcore (Lossless)",
    "Hardcore, Extreme (Hi-Res)",

    "Industrial, EBM, Dark Electro",
    "Industrial, EBM, Dark Electro (Lossless)",
    "Synthpop, New Wave",
    "Synthpop, New Wave (Lossless)",
    "Synthpop, New Wave, Retro (Hi-Res)",
    "IDM",
    "IDM (Lossless)",
    "Experimental Electronic",
    "Radioshow, Live Mixes",
    "Label-Packs",
    "Easy listening",

    "Rap, Hip-hop, RnB, Reggae",
    "Rap, Hip-hop зарубежный",
    "Rap, Hip-hop зарубежный (Lossless)",
    "Rap, Hip-hop отечественный",
    "Rap, Hip-hop отечественный (Lossless)",
    "RnB, Reggae",
    "RnB, Reggae (Lossless)",

    "Asian Music",
    "Asian Music (Hi-Res)",
    "Asian Pop",
    "Asian Pop (Lossless)",
    "Asian Rock, Metal",
    "Asian Rock, Metal (Lossless)",
    "Asian Traditional, Ethnic",
    "Asian Traditional, Ethnic (Lossless)",
    "Doujin Music",
    "Doujin Music (Lossless)",
    "Other Asian",
    "Other Asian (Lossless)",

    "Instrumental",
    "Instrumental (Hi-Res)",
    "Instrumental (Lossless)",
    "New Age/Meditative/Relax",
    "New Age/Meditative/Relax (Lossless)",
    "Folk",
    "Folk (Hi-Res)",
    "Folk (Lossless)",
    "OST",
    "OST (Hi-Res)",
    "OST (Lossless)",
    "Other",
    "Other (Lossless)",

    "Неофициальные сборники",
    "Jazz, Blues, Soul (сборники)",
    "Rock, Alternative, Punk, Metal (сборники)",
    "Pop (сборники)",
    "Electronic (сборники)",
    "Rap, Hip-hop, RnB, Reggae (сборники)",
    "Instrumental/New Age/Meditative/Relax (сборники)",
    "Прочее (сборники)",

    "Музыка (AAC)",
    "Архив Музыки",
]

categories_anime_anilibria = ["anime"]

categories_cinema_x1337 = ["flaticon-documentary", "flaticon-3d", "flaticon-divx", "flaticon-divx", "flaticon-video-dual-sound", "flaticon-dvd", "flaticon-h264", "flaticon-hd", "flaticon-hd", "flaticon-mp4", "flaticon-svcd", "flaticon-hd"]

categories_anime_x1337 = ["flaticon-anime", "flaticon-ninja-portrait", "flaticon-video-dual-sound", "flaticon-divx", "flaticon-divx", "flaticon-divx"]

categories_music_x1337 = ["flaticon-aac-file-type-rounded-rectangular-solid-interface-symbol", "flaticon-album", "flaticon-boxset", "flaticon-concert", "flaticon-discography", "flaticon-dvd", "flaticon-lossless", "flaticon-mp3", "flaticon-music-other", "flaticon-radio", "flaticon-music-single", "flaticon-music-video"]

categories_soft_x1337 = ["flaticon-android", "flaticon-apple", "flaticon-linux", "flaticon-mac", "flaticon-other", "flaticon-apps"]

categories_game_x1337 = ["flaticon-nds", "flaticon-dreamcast", "flaticon-nds", "flaticon-gamecube", "flaticon-old-joystick", "flaticon-apps", "flaticon-playstation", "flaticon-playstation", "flaticon-playstation", "flaticon-playstation", "flaticon-psp", "flaticon-psp", "flaticon-wii", "flaticon-xbox", "flaticon-xbox"]


MEDIA_EXTENSIONS = [
    [['lossless','Lossless', 'lossy', 'Lossy', 'Hi-Res stereo', 'многоканальная музыка', 'оцифровки', 'Hi-Res', 'сборники'],
     TORRENT_FOLDER_MUSIC, "in", "music", JELLYFIN_FOLDER_MUSIC],

    [['Апмиксы-Upmixes', 'Конверсии Blu-Ray, ADVD и DVD-Audio', 'Конверсии SACD', 'Конверсии Quadraphonic'],
     TORRENT_FOLDER_MUSIC, "==", "music", JELLYFIN_FOLDER_MUSIC],

    [categories_music_x1337 + categories_music_nnmclub,
     TORRENT_FOLDER_MUSIC, "==", "music", JELLYFIN_FOLDER_MUSIC],

    [categories_anime_x1337 + categories_anime_anilibria + categories_anime_rutr + categories_anime_nnmclub,
     TORRENT_FOLDER_ANIME, "==", "anime", JELLYFIN_FOLDER_ANIME],

    [categories_cinema_rutr + categories_cinema_x1337 + categories_cinema_nnmclub,
     TORRENT_FOLDER_CINEMA, "==", "cinema", JELLYFIN_FOLDER_CINEMA],

    [['фильмы', 'кино', 'мультфильмы', 'Фильмы', 'Мультсериалы', 'кинематографа', 'DVD Видео', 'HD Видео', '(Видео)'],
     TORRENT_FOLDER_CINEMA, "in", "cinema", JELLYFIN_FOLDER_CINEMA],

    [categories_game_rutr + categories_game_x1337 + categories_game_nnmclub,
     TORRENT_FOLDER_GAME, "==", "game", JELLYFIN_FOLDER_GAME],

    [categories_soft_rutr + categories_soft_x1337 + categories_soft_nnmclub,
     TORRENT_FOLDER_SOFT, "==", "soft", JELLYFIN_FOLDER_SOFT],

    [[],
     TORRENT_FOLDER_OTHER, "in", "other", JELLYFIN_FOLDER_OTHER],
    ]

log_file_encoding = "cp1251" if os.name == "nt" else "utf-8"

if os.name == 'nt':
    if SYMLINK_HOST not in ["127.0.0.1", "localhost"] and SYMLINK_IS_SSH:
       pass
    else:
        print("os.name == 'nt' -> JELLYFIN_ENABLE = False")
        JELLYFIN_ENABLE = False