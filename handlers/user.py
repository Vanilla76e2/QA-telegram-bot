import asyncio
from aiogram import types
from aiogram.filters import Command
from loader import dp, bot
from database import SessionLocal
from models import Question
from config import WORK_CHAT_ID
from keyboards import user_main_keyboard, manager_main_keyboard, generate_status_buttons
from logger import logger  # наш логгер
from datetime import datetime
from collections import defaultdict
from helpers import send_user_question_to_managers

# словарь для хранения последнего времени отправки вопроса пользователем
user_last_message = {}
MIN_INTERVAL = 60  # секунды
media_groups = defaultdict(list)
MEDIA_GROUP_TIMEOUT = 1.0

# =========================
# Команда /start
# =========================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if message.chat.id == WORK_CHAT_ID:
        # Меню для менеджера
        await message.answer(
            "Меню менеджера:",
            reply_markup=manager_main_keyboard()
        )
        logger.info(f"Менеджер {message.from_user.id} открыл меню.")
    elif message.chat.type == "private":
        # Меню для обычного пользователя
        await message.answer(
            "Привет! Можешь отправить свой вопрос или нажми кнопку ниже:",
            reply_markup=user_main_keyboard()
        )
        logger.info(f"Пользователь {message.from_user.id} открыл меню.")


# =========================
# Кнопка "Задать вопрос"
# =========================
@dp.message(lambda m: m.chat.type == "private" and m.text == "Задать вопрос")
async def ask_question_button(message: types.Message):
    await message.answer("Напишите ваш вопрос одним сообщением.")
    logger.info(f"Пользователь {message.from_user.id} нажал кнопку 'Задать вопрос'.")


# =========================
# Получение обычного текстового сообщения от пользователя
# =========================
@dp.message(lambda m: m.chat.type == "private" and not (m.text and m.text.startswith("/")))
async def receive_question(message: types.Message):
    user_id = message.from_user.id
    user_id = message.from_user.id 
    now = datetime.now()

    # собираем все сообщения группы, если есть media_group
    if message.media_group_id:
        key = (user_id, message.media_group_id)
        media_groups[key].append(message)
        await asyncio.sleep(MEDIA_GROUP_TIMEOUT)  # ждем остальные сообщения группы
        messages = media_groups.pop(key)
    else:
        messages = [message]

    # собираем текст и медиа
    text = None
    media_list = []
    for msg in messages:
        if msg.text or msg.caption:
            text = msg.text or msg.caption
        if msg.photo:
            media_list.append({"type": "photo", "file_id": msg.photo[-1].file_id})
        if msg.video:
            media_list.append({"type": "video", "file_id": msg.video.file_id})
        if msg.document:
            media_list.append({"type": "document", "file_id": msg.document.file_id})
        if msg.audio:
            media_list.append({"type": "audio", "file_id": msg.audio.file_id})

    # если текст отсутствует — просим пользователя написать вопрос
    if not text:
        await messages[0].answer("Пожалуйста, отправьте вопрос вместе с файлом.")
        return

    last_time = user_last_message.get(user_id) 
    if last_time and (now - last_time).total_seconds() < MIN_INTERVAL: 
        await message.answer(f"⏳ Пожалуйста, подождите {MIN_INTERVAL} секунд перед следующим вопросом.") 
        return 
    
    user_last_message[user_id] = now

    # сохраняем вопрос в базу
    try:
        with SessionLocal() as session:
            q = Question(
                user_id=user_id,
                username=message.from_user.username,
                text=text,
                media=media_list or None
            )
            session.add(q)
            session.commit()
            session.refresh(q)

        await messages[0].answer(f"Ваш вопрос принят! Номер: {q.id}")
        logger.info(f"Пользователь {user_id} создал вопрос #{q.id}.")

        # пересылаем в чат менеджеров через универсальную функцию
        await send_user_question_to_managers(
            text=f"Новый вопрос #{q.id} от @{q.username or 'пользователь'}:\n{text}",
            media_list=media_list,
            reply_markup=generate_status_buttons(q.id)
        )

        logger.info(f"Вопрос #{q.id} отправлен в рабочий чат.")
    except Exception as e:
        logger.error(f"Ошибка при создании вопроса от пользователя {user_id}: {e}")

