from aiogram import types


def get_keyboard_preferences(restrict_comms, pin, share, reply_post):
    if restrict_comms:
        comms = 'Отключить комментарии'
    else:
        comms = 'Включить комментарии'
    if pin:
        pin_text = 'Закрепить: вкл'
    else:
        pin_text = 'Закрепить: откл'
    if share:
        share_text = 'Поделиться: вкл'
    else:
        share_text = 'Поделиться: откл'
    if reply_post:
        reply = 'Ответный пост: вкл'
    else:
        reply = 'Ответный пост: выкл'
    buttons = [
        [types.InlineKeyboardButton(text="Изменить сообщение", callback_data="prf_edit")],
       # [types.InlineKeyboardButton(text="Изменить фото", callback_data="prf_edit_photo")],
        [types.InlineKeyboardButton(text="Реакции", callback_data="prf_reactions"),
         types.InlineKeyboardButton(text="URL-кнопки", callback_data="prf_buttons")],
        [types.InlineKeyboardButton(text="Скрытое продолжение", callback_data="prf_continuation")],
        [types.InlineKeyboardButton(text="Добавить гиперссылку", callback_data="prf_link")],
        [types.InlineKeyboardButton(text="🕭", callback_data="prf_notifications")],
        [types.InlineKeyboardButton(text=comms, callback_data="prf_disable_comms"+str(not restrict_comms))],
        [types.InlineKeyboardButton(text="Репост: откл", callback_data="prf_repost_on"),
         types.InlineKeyboardButton(text=pin_text, callback_data="prf_pin"+str(not pin)),
         types.InlineKeyboardButton(text=share_text, callback_data="prf_share"+str(not share))],
        [types.InlineKeyboardButton(text=reply, callback_data="prf_reply"+str(not reply_post))],
        [types.InlineKeyboardButton(text="Всё", callback_data="prf_end")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
def get_keyboard_preferences_repost(pin):
    if pin:
        pin_text = 'Закрепить: вкл'
    else:
        pin_text = 'Закрепить: откл'
    buttons = [
        [types.InlineKeyboardButton(text="🕭", callback_data="prf_notifications")],
        [types.InlineKeyboardButton(text="Репост: вкл", callback_data="prf_repost_off"),
         types.InlineKeyboardButton(text=pin_text, callback_data="prf_pin"+str(not pin))]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard