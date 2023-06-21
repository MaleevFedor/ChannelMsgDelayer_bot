from aiogram import types


def get_keyboard_world():
    buttons = [
        [types.InlineKeyboardButton(text="Европа", callback_data="tmz_Europe")],
        [types.InlineKeyboardButton(text="Азиатская часть России и СНГ", callback_data="tmz_Asia")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_keyboard_europe():
    buttons = [
        [types.InlineKeyboardButton(text="UTC-1", callback_data="UTC_-1")],
        [types.InlineKeyboardButton(text="UTC", callback_data="UTC_0")],
        [types.InlineKeyboardButton(text="UTC+1", callback_data="UTC_+1")],
        [types.InlineKeyboardButton(text="UTC+2", callback_data="UTC_+2")],
        [types.InlineKeyboardButton(text="UTC+3", callback_data="UTC_+3")],
        [types.InlineKeyboardButton(text="UTC+4", callback_data="UTC_+4")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_keyboard_asia():
    buttons = [
        [types.InlineKeyboardButton(text="UTC+5", callback_data="UTC_+5")],
        [types.InlineKeyboardButton(text="UTC+6", callback_data="UTC_+6")],
        [types.InlineKeyboardButton(text="UTC+7", callback_data="UTC_+7")],
        [types.InlineKeyboardButton(text="UTC+8", callback_data="UTC_+8")],
        [types.InlineKeyboardButton(text="UTC+9", callback_data="UTC_+9")],
        [types.InlineKeyboardButton(text="UTC+10", callback_data="UTC_+10")],
        [types.InlineKeyboardButton(text="UTC+11", callback_data="UTC_+11")],
        [types.InlineKeyboardButton(text="UTC+12", callback_data="UTC_+12")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
