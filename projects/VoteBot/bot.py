import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, \
    InputMediaPhoto
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import json
import os
from collections import Counter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ваш токен
BOT_TOKEN = "8352069823:AAHxp052jJg-1U5iMupOQMGFVDZtziafTP0"
ADMINS = [8238212300, 5581345556]

# Пути к файлам данных
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

NOMINATIONS_FILE = f"{DATA_DIR}/nominations.json"
CANDIDATES_FILE = f"{DATA_DIR}/candidates.json"
MEMES_FILE = f"{DATA_DIR}/memes.json"
VOTES_FILE = f"{DATA_DIR}/votes.json"
USERS_FILE = f"{DATA_DIR}/users.json"
SETTINGS_FILE = f"{DATA_DIR}/settings.json"

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ===== СОСТОЯНИЯ =====
class AdminStates(StatesGroup):
    waiting_for_nomination_name = State()
    waiting_for_nomination_description = State()
    waiting_for_candidate_name = State()
    waiting_for_meme_name = State()
    waiting_for_meme_photo = State()
    waiting_for_bulk_candidates = State()
    waiting_for_settings_value = State()
    waiting_for_broadcast_message = State()


class UserStates(StatesGroup):
    waiting_for_feedback = State()


# ===== УТИЛИТЫ ДЛЯ РАБОТЫ С ДАННЫМИ =====
def load_json(file_path, default=None):
    """Загрузка JSON файла"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки {file_path}: {e}")
    return default if default is not None else {}


def save_json(data, file_path):
    """Сохранение в JSON файл"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения {file_path}: {e}")
        return False


def load_nominations():
    return load_json(NOMINATIONS_FILE, {
        "37QUEEN": "Какая девушка заслужила номинацию королевы?",
        "37KING": "Какой парень удостоился номинации короля?",
        "ЧЕЛОВЕК-МЕМ ГОДА": "С каким человеком больше всего мемов?",
        "ФРИК ГОДА": "Кто выделился нестандартным поведением?",
        "МЕМ ГОДА": "Самый смешной мем года"
    })


def save_nominations(nominations):
    return save_json(nominations, NOMINATIONS_FILE)


def load_candidates():
    return load_json(CANDIDATES_FILE, {})


def save_candidates(candidates):
    return save_json(candidates, CANDIDATES_FILE)


def load_memes():
    return load_json(MEMES_FILE, {})


def save_memes(memes):
    return save_json(memes, MEMES_FILE)


def load_votes():
    return load_json(VOTES_FILE, {})


def save_votes(votes):
    return save_json(votes, VOTES_FILE)


def load_users():
    return load_json(USERS_FILE, {})


def save_users(users):
    return save_json(users, USERS_FILE)


def load_settings():
    return load_json(SETTINGS_FILE, {
        "voting_enabled": True,
        "results_visible": False,
        "max_votes_per_user": 10
    })


def save_settings(settings):
    return save_json(settings, SETTINGS_FILE)


# ===== КЛАВИАТУРЫ =====
def get_main_keyboard(user_id=None):
    """Основная клавиатура для пользователей"""
    buttons = [
        [KeyboardButton(text="Начать голосование")],
        [KeyboardButton(text="Мои голоса"), KeyboardButton(text="Топы")],
        [KeyboardButton(text="Обратная связь"), KeyboardButton(text="О премии")]
    ]
    if user_id and is_admin(user_id):
        buttons.append([KeyboardButton(text="Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_admin_keyboard():
    """Клавиатура для админов"""
    buttons = [
        [KeyboardButton(text="Управление номинациями"), KeyboardButton(text="Управление кандидатами")],
        [KeyboardButton(text="Управление мемами"), KeyboardButton(text="Статистика и результаты")],
        [KeyboardButton(text="Настройки системы"), KeyboardButton(text="Рассылка")],
        [KeyboardButton(text="Режим пользователя")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_nominations_management_keyboard():
    """Клавиатура управления номинациями"""
    buttons = [
        [InlineKeyboardButton(text="Добавить номинацию", callback_data="admin_add_nomination")],
        [InlineKeyboardButton(text="Удалить номинацию", callback_data="admin_delete_nomination")],
        [InlineKeyboardButton(text="Список номинаций", callback_data="admin_list_nominations")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_candidates_management_keyboard():
    """Клавиатура управления кандидатами"""
    buttons = [
        [InlineKeyboardButton(text="Добавить кандидата", callback_data="admin_add_candidate")],
        [InlineKeyboardButton(text="Добавить несколько", callback_data="admin_bulk_candidates")],
        [InlineKeyboardButton(text="Удалить кандидата", callback_data="admin_delete_candidate")],
        [InlineKeyboardButton(text="Список кандидатов", callback_data="admin_list_candidates")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_memes_management_keyboard():
    """Клавиатура управления мемами"""
    buttons = [
        [InlineKeyboardButton(text="Добавить мем", callback_data="admin_add_meme")],
        [InlineKeyboardButton(text="Удалить мем", callback_data="admin_delete_meme")],
        [InlineKeyboardButton(text="Список мемов", callback_data="admin_list_memes")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_stats_keyboard():
    """Клавиатура статистики"""
    buttons = [
        [InlineKeyboardButton(text="Общая статистика", callback_data="admin_general_stats")],
        [InlineKeyboardButton(text="Победители", callback_data="admin_winners")],
        [InlineKeyboardButton(text="Активность", callback_data="admin_activity")],
        [InlineKeyboardButton(text="Детальные результаты", callback_data="admin_detailed_results")],
        [InlineKeyboardButton(text="Обновить", callback_data="admin_refresh_stats")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_settings_keyboard():
    """Клавиатура настроек"""
    settings = load_settings()
    voting_status = "Выкл" if not settings["voting_enabled"] else "Вкл"
    results_status = "Скрыты" if not settings["results_visible"] else "Видны"

    buttons = [
        [InlineKeyboardButton(text=f"Голосование: {voting_status}", callback_data="admin_toggle_voting")],
        [InlineKeyboardButton(text=f"Результаты: {results_status}", callback_data="admin_toggle_results")],
        [InlineKeyboardButton(text="Лимит голосов", callback_data="admin_change_limit")],
        [InlineKeyboardButton(text="Сброс голосов", callback_data="admin_reset_votes")],
        [InlineKeyboardButton(text="Экспорт данных", callback_data="admin_export_data")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def is_admin(user_id):
    return user_id in ADMINS


def update_user_data(user_id, username, first_name, last_name):
    """Обновление данных пользователя"""
    users = load_users()
    users[str(user_id)] = {
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "last_active": datetime.now().isoformat(),
        "registered": users.get(str(user_id), {}).get("registered", datetime.now().isoformat())
    }
    save_users(users)


def get_user_votes_count(user_id):
    """Получение количества голосов пользователя"""
    votes = load_votes()
    return len(votes.get(str(user_id), {}))


def can_user_vote(user_id):
    """Проверка возможности голосования"""
    settings = load_settings()
    if not settings["voting_enabled"]:
        return False, "Голосование временно приостановлено!"

    votes_count = get_user_votes_count(user_id)
    if votes_count >= settings["max_votes_per_user"]:
        return False, f"Вы исчерпали лимит голосов ({settings['max_votes_per_user']})!"

    return True, ""


# ===== КОМАНДЫ =====
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    update_user_data(user.id, user.username, user.first_name, user.last_name)

    welcome_text = (
        "Добро пожаловать на премию *37AWARDS*!\n\n"
        "*Что здесь происходит?*\n"
        "• Голосуйте за лучших в разных номинациях\n"
        "• Следите за рейтингами в реальном времени\n"
        "• Участвуйте в выборе короля и королевы года\n\n"
        "*Как это работает?*\n"
        "1. Нажмите \"Начать голосование\"\n"
        "2. Выберите номинацию\n"
        "3. Отдайте голос за понравившегося кандидата\n\n"
        "Вы можете в любой момент посмотреть свои голоса и общую статистику!"
    )

    if is_admin(user.id):
        await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_admin_keyboard())
        await message.answer("*Режим администратора активирован*", parse_mode="Markdown")
    else:
        await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard(user.id))


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "*Помощь по боту*\n\n"
        "*Основные команды:*\n"
        "• /start - начать работу\n"
        "• /help - эта справка\n"
        "• /stats - моя статистика\n\n"
        "*Основные кнопки:*\n"
        "• Начать голосование - выбор номинаций\n"
        "• Мои голоса - просмотр ваших выборов\n"
        "• Топы - рейтинги и лидеры\n"
        "• Обратная связь - предложения и жалобы\n\n"
        "*Возникли проблемы?*\n"
        "Напишите нам через \"Обратную связь\"!"
    )
    await message.answer(help_text, parse_mode="Markdown")


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = str(message.from_user.id)
    votes = load_votes()
    user_votes = votes.get(user_id, {})

    stats_text = (
        f"*Ваша статистика*\n\n"
        f"*Проголосовали в:* {len(user_votes)} номинациях\n"
        f"*Осталось голосов:* {load_settings()['max_votes_per_user'] - len(user_votes)}\n\n"
    )

    if user_votes:
        stats_text += "*Ваши выборы:*\n"
        for nom, choice in user_votes.items():
            stats_text += f"• *{nom}*: {choice}\n"
    else:
        stats_text += "*Вы еще не голосовали*\nИспользуйте \"Начать голосование\"!"

    await message.answer(stats_text, parse_mode="Markdown")


@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Операция отменена", reply_markup=get_main_keyboard(message.from_user.id))


# ===== ОСНОВНОЙ ФУНКЦИОНАЛ =====
@dp.message(F.text == "Начать голосование")
async def start_voting(message: types.Message):
    user_id = message.from_user.id
    can_vote, error_msg = can_user_vote(user_id)

    if not can_vote:
        await message.answer(error_msg)
        return

    nominations = load_nominations()

    if not nominations:
        await message.answer("Номинаций пока нет, но скоро появятся!")
        return

    # Показываем прогресс голосования
    votes = load_votes()
    user_votes = votes.get(str(user_id), {})
    voted_count = len(user_votes)
    total_nominations = len(nominations)

    progress_text = f"Ваш прогресс: {voted_count}/{total_nominations}"
    if voted_count > 0:
        progress_percent = (voted_count / total_nominations) * 100
        progress_text += f" ({progress_percent:.1f}%)"

    keyboard = []
    for nomination in nominations.keys():
        status = "✅" if nomination in user_votes else "⚪"
        keyboard.append([InlineKeyboardButton(
            text=f"{status} {nomination}",
            callback_data=f"nom_{nomination}"
        )])

    keyboard.append([InlineKeyboardButton(text="Обновить", callback_data="refresh_voting")])

    await message.answer(
        f"{progress_text}\n\nВыберите номинацию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@dp.message(F.text == "Мои голоса")
async def show_my_votes(message: types.Message):
    user_id = str(message.from_user.id)
    votes = load_votes()
    nominations = load_nominations()
    memes = load_memes()

    if user_id not in votes or not votes[user_id]:
        await message.answer(
            "Вы еще не голосовали.\n\n"
            "Нажмите \"Начать голосование\" чтобы отдать свой голос!",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    user_votes = votes[user_id]
    votes_text = "*Ваши голоса:*\n\n"

    for nomination, choice in user_votes.items():
        if nomination in nominations:
            description = nominations[nomination]
            votes_text += f"*{nomination}*\n"
            votes_text += f"{description}\n"

            if nomination == "МЕМ ГОДА" and choice in memes:
                votes_text += f"*Ваш выбор:* {choice}\n"
                votes_text += "(мем с картинкой)\n"
            else:
                votes_text += f"*Ваш выбор:* {choice}\n"

            votes_text += "\n"
        else:
            votes_text += f"*{nomination}* (номинация удалена)\n"
            votes_text += f"*Ваш выбор:* {choice}\n\n"

    keyboard = [
        [InlineKeyboardButton(text="Продолжить голосование", callback_data="continue_voting")],
        [InlineKeyboardButton(text="Изменить голоса", callback_data="change_votes")],
        [InlineKeyboardButton(text="Очистить все голоса", callback_data="clear_all_votes")]
    ]

    await message.answer(votes_text, parse_mode="Markdown",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


@dp.message(F.text == "Топы")
async def show_tops(message: types.Message):
    settings = load_settings()
    if not settings["results_visible"] and not is_admin(message.from_user.id):
        await message.answer("Результаты пока скрыты. Следите за анонсами!")
        return

    votes = load_votes()
    nominations = load_nominations()

    if not votes:
        await message.answer("Голосов пока нет. Будьте первыми!")
        return

    tops_text = "*Текущие лидеры*\n\n"

    for nomination in nominations:
        if nomination == "МЕМ ГОДА":
            continue

        nomination_votes = []
        for user_votes in votes.values():
            if nomination in user_votes:
                nomination_votes.append(user_votes[nomination])

        if nomination_votes:
            vote_count = Counter(nomination_votes)
            top_candidate = vote_count.most_common(1)[0]

            tops_text += f"*{nomination}*\n"
            tops_text += f"*Лидер:* {top_candidate[0]}\n"
            tops_text += f"*Голосов:* {top_candidate[1]}\n\n"

    # Добавляем общую статистику
    total_voters = len(votes)
    total_votes = sum(len(user_votes) for user_votes in votes.values())

    tops_text += f"*Общая статистика:*\n"
    tops_text += f"• *Участников:* {total_voters}\n"
    tops_text += f"• *Всего голосов:* {total_votes}\n"
    tops_text += f"• *Номинаций:* {len(nominations)}\n"

    await message.answer(tops_text, parse_mode="Markdown")


@dp.message(F.text == "Обратная связь")
async def feedback_start(message: types.Message, state: FSMContext):
    await message.answer(
        "*Обратная связь*\n\n"
        "Напишите ваше предложение, жалобу или идею для улучшения премии.\n"
        "Мы внимательно изучим каждое сообщение!\n\n"
        "*Чтобы отменить отправку, используйте /cancel*",
        parse_mode="Markdown"
    )
    await state.set_state(UserStates.waiting_for_feedback)


@dp.message(UserStates.waiting_for_feedback)
async def feedback_receive(message: types.Message, state: FSMContext):
    feedback_text = message.text
    user = message.from_user

    # Сохраняем feedback в отдельный файл или отправляем админам
    feedback_data = load_json(f"{DATA_DIR}/feedback.json", [])
    feedback_data.append({
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "text": feedback_text,
        "timestamp": datetime.now().isoformat()
    })
    save_json(feedback_data, f"{DATA_DIR}/feedback.json")

    # Уведомляем админов
    for admin_id in ADMINS:
        try:
            await bot.send_message(
                admin_id,
                f"*Новый отзыв*\n\n"
                f"*Пользователь:* {user.first_name} (@{user.username})\n"
                f"*ID:* {user.id}\n"
                f"*Текст:* {feedback_text}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")

    await message.answer(
        "*Спасибо за ваш отзыв!*\n"
        "Мы обязательно рассмотрим ваше сообщение.",
        parse_mode="Markdown"
    )
    await state.clear()


@dp.message(F.text == "О премии")
async def about_premium(message: types.Message):
    about_text = (
        "*О премии 37AWARDS*\n\n"
        "*Что это?*\n"
        "37AWARDS - это ежегодная премия, где сообщество выбирает самых ярких представителей года в различных номинациях.\n\n"
        "*Цели:*\n"
        "• Выявить самых популярных и влиятельных участников\n"
        "• Отметить нестандартные достижения и таланты\n"
        "• Создать архив memorable моментов года\n\n"
        "*Как участвовать?*\n"
        "• Голосуйте за понравившихся кандидатов\n"
        "• Предлагайте новые номинации через обратную связь\n"
        "• Следите за результатами в реальном времени\n\n"
        "*Номинации обновляются регулярно!*"
    )
    await message.answer(about_text, parse_mode="Markdown")


# ===== АДМИН ПАНЕЛЬ =====
@dp.message(F.text == "Админ-панель")
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещен")
        return

    admin_text = (
        "*Панель администратора*\n\n"
        "*Статистика системы:*\n"
        f"• Пользователей: {len(load_users())}\n"
        f"• Голосов: {sum(len(v) for v in load_votes().values())}\n"
        f"• Номинаций: {len(load_nominations())}\n"
        f"• Кандидатов: {sum(len(c) for c in load_candidates().values())}\n\n"
        "Выберите раздел для управления:"
    )

    keyboard = [
        [InlineKeyboardButton(text="Управление номинациями", callback_data="admin_nominations")],
        [InlineKeyboardButton(text="Управление кандидатами", callback_data="admin_candidates")],
        [InlineKeyboardButton(text="Управление мемами", callback_data="admin_memes")],
        [InlineKeyboardButton(text="Статистика и результаты", callback_data="admin_stats")],
        [InlineKeyboardButton(text="Настройки системы", callback_data="admin_settings")],
        [InlineKeyboardButton(text="Рассылка", callback_data="admin_broadcast")]
    ]

    await message.answer(admin_text, parse_mode="Markdown",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


@dp.message(F.text == "Режим пользователя")
async def user_mode(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "Переключен в режим пользователя",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


# ===== CALLBACK ОБРАБОТЧИКИ =====
@dp.callback_query(F.data.startswith("nom_"))
async def handle_nomination_selection(callback: types.CallbackQuery):
    nomination = callback.data.replace("nom_", "")
    user_id = callback.from_user.id

    can_vote, error_msg = can_user_vote(user_id)
    if not can_vote:
        await callback.answer(error_msg, show_alert=True)
        return

    nominations = load_nominations()

    if nomination not in nominations:
        await callback.answer("Номинация не найдена")
        return

    # Для номинации "МЕМ ГОДА" показываем мемы с картинками
    if nomination == "МЕМ ГОДА":
        memes = load_memes()

        if not memes:
            keyboard = [[InlineKeyboardButton(text="Назад", callback_data="back_to_nominations")]]
            await callback.message.edit_text(
                f"{nomination}\n\n{nominations[nomination]}\n\nМемов пока нет!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
        else:
            first_meme_name = list(memes.keys())[0]
            await show_meme_with_navigation(callback, nomination, first_meme_name, 0)
    else:
        # Для обычных номинаций показываем кандидатов
        candidates = load_candidates()
        nomination_candidates = candidates.get(nomination, [])

        if not nomination_candidates:
            keyboard = [[InlineKeyboardButton(text="Назад", callback_data="back_to_nominations")]]
            await callback.message.edit_text(
                f"{nomination}\n\n{nominations[nomination]}\n\nКандидатов пока нет!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
        else:
            keyboard = []
            for candidate in nomination_candidates:
                keyboard.append([InlineKeyboardButton(
                    text=candidate,
                    callback_data=f"vote_{nomination}_{candidate}"
                )])

            keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back_to_nominations")])

            await callback.message.edit_text(
                f"{nomination}\n\n{nominations[nomination]}\n\nВыберите кандидата:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )

    await callback.answer()


@dp.callback_query(F.data.startswith("vote_"))
async def handle_voting(callback: types.CallbackQuery):
    data = callback.data.replace("vote_", "")
    nomination, candidate = data.rsplit("_", 1)

    user_id = str(callback.from_user.id)
    votes = load_votes()

    if user_id not in votes:
        votes[user_id] = {}

    # Проверяем, не голосовал ли уже пользователь в этой номинации
    old_choice = votes[user_id].get(nomination)
    votes[user_id][nomination] = candidate
    save_votes(votes)

    if old_choice:
        await callback.answer(f"Голос изменен: {old_choice} → {candidate}")
    else:
        await callback.answer(f"Вы проголосовали за {candidate}!")

    await show_nominations_list(callback)


@dp.callback_query(F.data.startswith("memevote_"))
async def handle_meme_voting(callback: types.CallbackQuery):
    data = callback.data.replace("memevote_", "")
    nomination, meme_name = data.rsplit("_", 1)

    user_id = str(callback.from_user.id)
    votes = load_votes()

    if user_id not in votes:
        votes[user_id] = {}

    old_choice = votes[user_id].get(nomination)
    votes[user_id][nomination] = meme_name
    save_votes(votes)

    if old_choice:
        await callback.answer(f"Голос изменен: {old_choice} → {meme_name}")
    else:
        await callback.answer(f"Вы проголосовали за мем \"{meme_name}\"!")

    await show_nominations_list(callback)


@dp.callback_query(F.data.startswith("meme_nav_"))
async def handle_meme_navigation(callback: types.CallbackQuery):
    data = callback.data.replace("meme_nav_", "")
    nomination, meme_name, index = data.rsplit("_", 2)

    await show_meme_with_navigation(callback, nomination, meme_name, int(index))
    await callback.answer()


@dp.callback_query(F.data == "back_to_nominations")
async def handle_back_to_nominations(callback: types.CallbackQuery):
    await show_nominations_list(callback)


@dp.callback_query(F.data == "refresh_voting")
async def handle_refresh_voting(callback: types.CallbackQuery):
    await show_nominations_list(callback)


@dp.callback_query(F.data == "continue_voting")
async def handle_continue_voting(callback: types.CallbackQuery):
    await show_nominations_list(callback)


# ===== АДМИН CALLBACKS =====
@dp.callback_query(F.data == "admin_nominations")
async def handle_admin_nominations(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await callback.message.edit_text(
        "*Управление номинациями*\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=get_nominations_management_keyboard()
    )


@dp.callback_query(F.data == "admin_add_nomination")
async def handle_admin_add_nomination(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    await callback.message.edit_text(
        "*Добавление номинации*\n\nВведите название номинации:",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_for_nomination_name)


@dp.callback_query(F.data == "admin_back")
async def handle_admin_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await admin_panel(callback.message)


# ===== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ =====
async def show_meme_with_navigation(callback: types.CallbackQuery, nomination: str, meme_name: str, current_index: int):
    memes = load_memes()
    meme_names = list(memes.keys())

    if current_index is None:
        current_index = meme_names.index(meme_name) if meme_name in meme_names else 0

    if meme_name not in memes:
        await callback.answer("Мем не найден")
        return

    meme_data = memes[meme_name]
    total_memes = len(meme_names)

    # Создаем клавиатуру для навигации
    keyboard = []

    # Кнопка выбора мема
    keyboard.append([InlineKeyboardButton(
        text=f"Выбрать этот мем: {meme_name}",
        callback_data=f"memevote_{nomination}_{meme_name}"
    )])

    # Кнопки навигации
    if total_memes > 1:
        prev_index = (current_index - 1) % total_memes
        next_index = (current_index + 1) % total_memes

        nav_buttons = [
            InlineKeyboardButton(text="⬅️",
                                 callback_data=f"meme_nav_{nomination}_{meme_names[prev_index]}_{prev_index}"),
            InlineKeyboardButton(text=f"{current_index + 1}/{total_memes}", callback_data="noop"),
            InlineKeyboardButton(text="➡️",
                                 callback_data=f"meme_nav_{nomination}_{meme_names[next_index]}_{next_index}")
        ]
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back_to_nominations")])

    caption = (f"{nomination}\n\n"
               f"Какой мем показался вам самым смешным в этом году?\n\n"
               f"Мем: {meme_name}\n"
               f"{current_index + 1} из {total_memes}")

    try:
        if callback.message.photo:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=meme_data['photo_id'], caption=caption),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
        else:
            await callback.message.delete()
            sent_message = await callback.message.answer_photo(
                photo=meme_data['photo_id'],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            # Сохраняем ID сообщения для дальнейших обновлений
            await callback.answer()
    except Exception as e:
        logger.error(f"Error handling meme: {e}")
        await callback.message.edit_text(
            "Ошибка загрузки мема",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Назад", callback_data="back_to_nominations")
            ]])
        )


async def show_nominations_list(callback: types.CallbackQuery):
    nominations = load_nominations()
    user_id = str(callback.from_user.id)
    votes = load_votes()
    user_votes = votes.get(user_id, {})

    keyboard = []
    for nomination in nominations.keys():
        status = "✅" if nomination in user_votes else "⚪"
        keyboard.append([InlineKeyboardButton(
            text=f"{status} {nomination}",
            callback_data=f"nom_{nomination}"
        )])

    voted_count = len(user_votes)
    total_nominations = len(nominations)
    progress_text = f"Прогресс: {voted_count}/{total_nominations}"

    try:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(
                f"Голос учтен!\n\n{progress_text}\n\nВыберите номинацию:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
        else:
            await callback.message.edit_text(
                f"Голос учтен!\n\n{progress_text}\n\nВыберите номинацию:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
    except Exception as e:
        logger.error(f"Error showing nominations: {e}")
        await callback.message.answer(
            f"Голос учтен!\n\n{progress_text}\n\nВыберите номинацию:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )


# ===== ОБРАБОТКА СОСТОЯНИЙ АДМИНА =====
@dp.message(AdminStates.waiting_for_nomination_name)
async def handle_nomination_name(message: types.Message, state: FSMContext):
    nomination_name = message.text.strip()
    await state.update_data(nomination_name=nomination_name)

    await message.answer(
        f"Название номинации: *{nomination_name}*\n\nТеперь введите описание номинации:",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_for_nomination_description)


@dp.message(AdminStates.waiting_for_nomination_description)
async def handle_nomination_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    nomination_name = data.get("nomination_name")
    nomination_description = message.text.strip()

    nominations = load_nominations()
    nominations[nomination_name] = nomination_description
    save_nominations(nominations)

    await message.answer(
        f"Номинация *{nomination_name}* успешно добавлена!",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )
    await state.clear()


# ===== ЗАПУСК БОТА =====
async def main():
    logger.info("Запуск бота...")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())