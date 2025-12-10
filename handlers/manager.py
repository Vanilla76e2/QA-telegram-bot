import asyncio
from aiogram import types
from aiogram.filters import Command, CommandObject
from aiogram.exceptions import TelegramRetryAfter
from loader import dp
from helpers import send_user_question_to_managers, get_questions, notify_user_status_change
from database import SessionLocal
from models import Question, STATUSES
from keyboards import (
    generate_question_list_page,
    generate_status_buttons,
    StatusCallback,
    PageQuestionCallback,
    PaginationCallback,
    QuestionCallback
)
from config import WORK_CHAT_ID
from logger import logger

QUESTIONS_PER_PAGE = 8

# -------------------------
# Меню "Список вопросов" для менеджера
# -------------------------
@dp.message(lambda m: m.chat.id == WORK_CHAT_ID and m.text == "📋 Список вопросов")
async def manager_list_btn(message: types.Message):
    # активные вопросы
    active_statuses = ["новый 🆕", "в работе ⚙️"]
    questions = get_questions(status_filter=active_statuses)  # get_questions сортирует по id.asc()

    if not questions:
        await message.answer("Активных вопросов нет.")
        return

    text, markup = generate_question_list_page(
        questions,
        page=1,
        per_page=QUESTIONS_PER_PAGE
    )
    await message.answer(text, reply_markup=markup)
    logger.info(f"Менеджер {message.from_user.id} открыл список вопросов.")

# -------------------------
# Пагинация вопросов
# -------------------------
@dp.callback_query(PaginationCallback.filter())
async def paginate_questions(callback: types.CallbackQuery, callback_data: PaginationCallback):
    # Маппим filter_status
    if callback_data.filter_status == "active":
        status_filter_list = ["новый 🆕", "в работе ⚙️"]
    else:
        status_filter_list = None

    questions = get_questions(status_filter=status_filter_list)

    # Генерируем всё в одном месте
    text, reply_markup = generate_question_list_page(
        questions,
        page=callback_data.page,
        per_page=QUESTIONS_PER_PAGE,
        filter_status=callback_data.filter_status
    )

    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramRetryAfter as e:
        logger.warning(f"Flood control: ждем {e.timeout} сек.")
        await asyncio.sleep(e.timeout)
        await callback.message.edit_text(text, reply_markup=reply_markup)

    await callback.answer()
    logger.info(
        f"Менеджер {callback.from_user.id} открыл страницу {callback_data.page}."
    )

# -------------------------
# Изменение статуса вопроса через кнопки
# -------------------------
@dp.callback_query(StatusCallback.filter())
async def change_status_callback(callback: types.CallbackQuery, callback_data: StatusCallback):
    with SessionLocal() as session:
        question = session.query(Question).filter_by(id=callback_data.question_id).first()
        if not question:
            await callback.answer("Вопрос не найден", show_alert=True)
            logger.warning(f"Вопрос {callback_data.question_id} не найден для смены статуса.")
            return
        question.status = callback_data.new_status
        session.commit()
        session.refresh(question)  # Добавьте эту строку здесь

    await notify_user_status_change(question)

    # Обновляем сообщение с новой клавиатурой
    await callback.message.edit_text(
        f"#{question.id} | {question.status} | @{question.username or 'пользователь'}:\n{question.text}",
        reply_markup=generate_status_buttons(question.id)
    )

    await callback.answer(f"Статус обновлён на '{question.status}'")
    logger.info(f"Статус вопроса #{question.id} обновлён на {question.status} менеджером {callback.from_user.id}.")

# -------------------------
# Выбор вопроса на странице
# -------------------------
@dp.callback_query(PageQuestionCallback.filter())
async def select_question_callback(callback: types.CallbackQuery, callback_data: PageQuestionCallback):
    questions = get_questions()
    start = (callback_data.page - 1) * QUESTIONS_PER_PAGE
    try:
        q = questions[start + callback_data.index]
    except IndexError:
        await callback.answer("Вопрос не найден", show_alert=True)
        logger.warning(f"Менеджер {callback.from_user.id} выбрал несуществующий вопрос на странице {callback_data.page}.")
        return

    await send_user_question_to_managers(
        text=f"#{q.id} | {q.status} | @{q.username or 'пользователь'}:\n{q.text}",
        media_list = q.media if q.media else [],
        reply_markup=generate_status_buttons(q.id)
    )
    await callback.answer()
    logger.info(f"Менеджер {callback.from_user.id} выбрал вопрос #{q.id}.")

# -------------------------
# Команда /status — ручная смена статуса
# -------------------------
@dp.message(Command("status"))
async def change_status(message: types.Message, command: CommandObject):
    if message.chat.id != WORK_CHAT_ID:
        return

    try:
        parts = message.text.split(maxsplit=2)
        q_id = int(parts[1])
        new_status = parts[2]
    except (IndexError, ValueError):
        await message.answer("Использование: /status <номер> <статус>")
        return

    if new_status not in STATUSES:
        await message.answer(f"Допустимые статусы: {', '.join(STATUSES)}")
        return

    with SessionLocal() as session:
        question = session.query(Question).filter_by(id=q_id).first()
        if not question:
            await message.answer("Вопрос с таким номером не найден.")
            return
        question.status = new_status
        session.commit()

    await notify_user_status_change(question)

    await send_user_question_to_managers(
        text=f"#{question.id} | {question.status} | @{question.username or 'пользователь'}:\n{question.text}",
        media_list=[],
        reply_markup=generate_status_buttons(question.id)
    )

    logger.info(f"Менеджер {message.from_user.id} изменил статус вопроса #{q_id} на '{new_status}'.")
