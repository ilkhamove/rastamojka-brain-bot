from io import BytesIO

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from openai import OpenAI

from src.keyboards import categories_keyboard, main_hint_keyboard
from src.db.session import SessionLocal
from src.db import models
from src.config import settings

router = Router()

openai_client = None
if settings.OPENAI_API_KEY:
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)




class AddKnowledgeStates(StatesGroup):
    waiting_for_media = State()
    waiting_for_category = State()
    waiting_for_description = State()


@router.message(F.text == "ℹ️ Как пользоваться")
async def help_handler(message: Message):
    text = (
        "ℹ️ Как пользоваться ботом «Мозг таможни»:\n\n"
        "1️⃣ Пришлите файл, фото или голосовое сообщение, связанное с таможней.\n"
        "2️⃣ Я спрошу, к какому разделу это относится (НПА, пояснения ТНВЭД, CMR и т.д.).\n"
        "3️⃣ Затем попрошу коротко описать материал своими словами.\n"
        "4️⃣ Всё сохраню в базу знаний.\n\n"
        "Попробуйте прямо сейчас — отправьте любой документ, фото или голосовое 👇"
    )
    await message.answer(text, reply_markup=main_hint_keyboard())


@router.message(AddKnowledgeStates.waiting_for_media, F.document | F.photo | F.voice)
@router.message(F.document | F.photo | F.voice)
async def handle_media(message: Message, state: FSMContext, bot: Bot):
    """
    Обрабатываем медиа: документ, фото или голосовое.
    Для голосового пытаемся сделать транскрипцию через OpenAI.
    """

    input_type: str | None = None
    telegram_file_id: str | None = None
    transcript_text: str | None = None

    # Документ
    if message.document:
        input_type = "document"
        telegram_file_id = message.document.file_id

    # Фото
    elif message.photo:
        input_type = "photo"
        telegram_file_id = message.photo[-1].file_id  # самое большое качество

    # Голосовое
    elif message.voice:
        input_type = "voice"
        telegram_file_id = message.voice.file_id

        if openai_client is not None:
            try:
                await message.answer("🎙 Обрабатываю голосовое сообщение, распознаю текст...")

                # Скачиваем voice в память
                voice_bytes = BytesIO()
                await bot.download(message.voice, voice_bytes)
                voice_bytes.seek(0)

                # OpenAI ждёт файловый объект с именем
                voice_bytes.name = "audio.ogg"

                resp = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=voice_bytes,
                )

                # Новые версии openai возвращают объект с полем text
                transcript_text = resp.text.strip() if getattr(resp, "text", None) else None

                if transcript_text:
                    preview = transcript_text
                    if len(preview) > 300:
                        preview = preview[:300] + "..."
                    await message.answer(
                        "✅ Голосовое сообщение распознано.\n"
                        f"Текст: <i>{preview}</i>",
                    )
                else:
                    await message.answer(
                        "⚠️ Не удалось распознать текст из голосового. "
                        "Я всё равно сохраню само голосовое сообщение."
                    )

            except Exception as e:
                # Логируем в консоль, чтобы видеть, что именно падает
                print("WHISPER ERROR:", repr(e))
                await message.answer(
                    "⚠️ Произошла ошибка при распознавании голосового. "
                    "Сохраню голос, но без текста."
                )
        else:
            await message.answer(
                "ℹ️ Голосовое сообщение сохраню как есть.\n"
                "Транскрипция не настроена (нет OPENAI_API_KEY)."
            )

    else:
        await message.answer(
            "Пожалуйста, пришлите файл, фото или голосовое сообщение.",
            reply_markup=main_hint_keyboard(),
        )
        return

    # Сохраняем временные данные в FSM
    await state.set_state(AddKnowledgeStates.waiting_for_category)
    await state.update_data(
        input_type=input_type,
        telegram_file_id=telegram_file_id,
        transcript=transcript_text,
    )

    await message.answer(
        "✅ Получил.\n\n"
        "Теперь выберите, к какому разделу относится этот материал:",
        reply_markup=categories_keyboard(),
    )


@router.message(AddKnowledgeStates.waiting_for_media)
async def handle_invalid_media(message: Message, state: FSMContext):
    """Если ждём медиа, а пользователь прислал текст."""
    await message.answer(
        "Сейчас я жду файл, фото или голосовое сообщение.\n"
        "Пожалуйста, отправьте материал, который нужно сохранить в базу.",
        reply_markup=main_hint_keyboard(),
    )


@router.callback_query(AddKnowledgeStates.waiting_for_category, F.data.startswith("cat_"))
async def handle_category(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    category_map = {
        "cat_npa": "npa",
        "cat_conclusions": "conclusions",
        "cat_tnved": "tnved",
        "cat_cmr": "cmr_invoice",
        "cat_predecision": "predecision",
        "cat_cases": "cases",
        "cat_other": "other",
        "cat_base": "base",
    }

    raw = callback.data
    category = category_map.get(raw, "other")

    await state.update_data(category=category)
    await state.set_state(AddKnowledgeStates.waiting_for_description)

    await callback.message.answer(
        "✏️ Кратко опишите этот материал простыми словами.\n\n"
        "Например: «Письмо ГТК по классификации электросамокатов»."
    )


@router.message(AddKnowledgeStates.waiting_for_description)
async def handle_description(message: Message, state: FSMContext):
    description = (message.text or "").strip()
    data = await state.get_data()

    input_type = data.get("input_type")
    telegram_file_id = data.get("telegram_file_id")
    category = data.get("category", "other")
    transcript = data.get("transcript")  # текст из голосового, если был

    if not input_type or not telegram_file_id:
        await message.answer(
            "⚠️ Что-то пошло не так с сохранением данных. Попробуйте отправить документ ещё раз."
        )
        await state.clear()
        return

    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            user = models.User(
                telegram_id=message.from_user.id,
                full_name=message.from_user.full_name,
                username=message.from_user.username,
            )
            db.add(user)
            db.flush()

        item = models.KnowledgeItem(
            user_id=user.id,
            input_type=input_type,
            telegram_file_id=telegram_file_id,
            category=category,
            description=description,
            transcript=transcript,
        )
        db.add(item)
        db.commit()
    except Exception:
        db.rollback()
        await message.answer(
            "⚠️ Произошла ошибка при сохранении записи. Попробуйте ещё раз позже."
        )
        return
    finally:
        db.close()

    await state.clear()

    await message.answer(
        "✅ Запись сохранена в «Мозг таможни».\n\n"
        "Можете отправить следующий документ, фото или голосовое сообщение.",
        reply_markup=main_hint_keyboard(),
    )
