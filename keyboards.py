from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters.callback_data import CallbackData
from models import STATUSES

# =========================
# Callback для смены статуса вопроса
# =========================
class StatusCallback(CallbackData, prefix="status"):
    question_id: int
    new_status: str

# =========================
# Кнопки для изменения статуса вопроса (для менеджера)
# =========================
def generate_status_buttons(question_id: int) -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру с кнопками для изменения статуса вопроса.
    Располагаем кнопки по 3 в ряд.
    """
    keyboard_rows = []
    row = []
    for i, status in enumerate(STATUSES, 1):
        btn = InlineKeyboardButton(
            text=status,
            callback_data=StatusCallback(question_id=question_id, new_status=status).pack()
        )
        row.append(btn)
        if i % 3 == 0:
            keyboard_rows.append(row)
            row = []
    if row:
        keyboard_rows.append(row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


# =========================
# Основные кнопки для пользователей и менеджеров
# =========================
def user_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для обычного пользователя
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Задать вопрос")]],
        resize_keyboard=True
    )

def manager_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для менеджера
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📋 Список вопросов")]],
        resize_keyboard=True
    )


# =========================
# Callback для фильтрации вопросов
# =========================
class StatusFilterCallback(CallbackData, prefix="filter"):
    status: str  # "all", "new", "in_progress", "done", "rejected"


# =========================
# Callback для выбора конкретного вопроса на странице
# =========================
class QuestionCallback(CallbackData, prefix="question"):
    question_id: int

class PaginationCallback(CallbackData, prefix="page"):
    page: int
    filter_status: str = "active"  # активные по умолчанию

class PageQuestionCallback(CallbackData, prefix="pq"):
    page: int        # текущая страница
    index: int       # индекс вопроса на странице (0..N-1)
    filter_status: str = "active"


# =========================
# Формирование текста страницы вопросов + кнопки пагинации
# =========================
def generate_question_list_page(questions, page=1, per_page=8, filter_status="active"):
    """
    Формирует текст и клавиатуру для страницы вопросов с пагинацией.
    filter_status: active / new / in_progress / all
    """
    # фильтруем по статусу
    if filter_status == "active":
        questions = [q for q in questions if q.status in ["новый 🆕", "в работе ⚙️"]]
    start = (page - 1) * per_page
    end = start + per_page
    page_questions = questions[start:end]

    # формируем текст с небольшим отступом для лучшей читаемости
    text = ""
    for i, q in enumerate(page_questions, 1):
        date_str = q.created_at.strftime("%d.%m.%Y %H:%M")
        text += f"{i}. #{q.id} | {q.status} | @{q.username or 'пользователь'} | {date_str}\n"
        text += f"   {q.text}\n\n"

    # кнопки выбора конкретного вопроса на странице (по 4 в ряд)
    keyboard = []
    row = []
    for i in range(len(page_questions)):
        row.append(
            InlineKeyboardButton(
                text=str(i + 1),
                callback_data=PageQuestionCallback(page=page, index=i, filter_status=filter_status).pack()
            )
        )
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # кнопки навигации между страницами
    nav_buttons = []
    if start > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀ Назад",
                callback_data=PaginationCallback(page=page-1, filter_status=filter_status).pack()
            )
        )
    if end < len(questions):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ▶",
                callback_data=PaginationCallback(page=page+1, filter_status=filter_status).pack()
            )
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)


# =========================
# Кнопки фильтрации списка вопросов
# =========================
def generate_filter_buttons() -> InlineKeyboardMarkup:
    """
    Inline клавиатура для фильтрации списка вопросов
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("Все", callback_data="filter:all"),
            InlineKeyboardButton("Новые", callback_data="filter:new"),
            InlineKeyboardButton("В работе", callback_data="filter:in_progress")
        ]
    ])
