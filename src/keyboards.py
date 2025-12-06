from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_hint_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура-подсказка — просто напоминает, что надо прислать файл/фото/голос."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ℹ️ Как пользоваться")],
        ],
        resize_keyboard=True,
    )


def categories_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-кнопки категорий для присланного материала."""
    buttons = [
        [InlineKeyboardButton(text="🧾 НПА (законы/постановления)", callback_data="cat_npa")],
        [InlineKeyboardButton(text="📄 Заключения / разъяснения", callback_data="cat_conclusions")],
        [InlineKeyboardButton(text="📦 Пояснения ТНВЭД", callback_data="cat_tnved")],
        [InlineKeyboardButton(text="🚛 ТСД / Логистика", callback_data="cat_cmr")],
        [InlineKeyboardButton(text="🧷 Предварительное решение таможни", callback_data="cat_predecision")],
        [InlineKeyboardButton(text="⚖️ Практика / кейсы", callback_data="cat_cases")],
        [InlineKeyboardButton(text="🌀 Другое", callback_data="cat_other")],
        [InlineKeyboardButton(text="🧠 База", callback_data="cat_base")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
