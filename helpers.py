from aiogram.types import InputMediaPhoto, InputMediaVideo
from loader import dp, bot
from config import WORK_CHAT_ID
from database import SessionLocal
from models import Question, STATUSES
from logger import logger

async def send_user_question_to_managers(
    text: str,
    media_list: list,
    reply_markup=None
):
    """
    Универсальный метод для пересылки вопроса пользователя в чат менеджеров
    с поддержкой media_group и кнопок.
    """
    from aiogram.types import InputMediaPhoto, InputMediaVideo
    from loader import bot
    from config import WORK_CHAT_ID

    if not media_list:
        await bot.send_message(WORK_CHAT_ID, text, reply_markup=reply_markup)
        return

    # 1 Сначала разделяем медиа
    photos_videos = [m for m in media_list if m["type"] in ("photo", "video")]
    other_media = [m for m in media_list if m["type"] not in ("photo", "video")]

    # 2 Отправляем фото/видео группой без caption
    if photos_videos:
        input_media = []
        for m in photos_videos:
            if m["type"] == "photo":
                input_media.append(InputMediaPhoto(media=m["file_id"]))
            elif m["type"] == "video":
                input_media.append(InputMediaVideo(media=m["file_id"]))

        await bot.send_media_group(WORK_CHAT_ID, input_media)

    # 3 Остальные файлы
    for m in other_media:
        if m["type"] == "document":
            await bot.send_document(WORK_CHAT_ID, m["file_id"])
        elif m["type"] == "audio":
            await bot.send_audio(WORK_CHAT_ID, m["file_id"])
    
    # 4 Текст с кнопками
    await bot.send_message(WORK_CHAT_ID, text, reply_markup=reply_markup)

def get_questions(status_filter: list[str] = None):
    with SessionLocal() as session:
        q = session.query(Question)
        if status_filter:
            q = q.filter(Question.status.in_(status_filter))
        return q.order_by(Question.id.asc()).all()
    
async def notify_user_status_change(question: Question):
    try:
        await bot.send_message(
            question.user_id,
            f"Ваш вопрос #{question.id} обновлён. Новый статус: {question.status}"
        )
    except Exception as e:
        logger.error(f"Ошибка при уведомлении пользователя: {e}")