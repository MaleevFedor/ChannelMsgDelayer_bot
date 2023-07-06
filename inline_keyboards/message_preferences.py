from aiogram import types
from emoji import emojize

tick = emojize(':heavy_check_mark:')
cross = emojize(':cross_mark_button:')
no_bell = emojize(':no_bell:')
bell = emojize(':bell:')


def get_keyboard_preferences(new_markup, is_media_group, restrict_comms, pin, share, reply_post, notifications_off):
    if restrict_comms:
        comms = 'Включить комментарии'
    else:
        comms = 'Отключить комментарии'
    if pin:
        pin_text = 'Закрепить: ' + tick
    else:
        pin_text = 'Закрепить: ' + cross
    if share:
        share_text = 'Поделиться: ' + tick
    else:
        share_text = 'Поделиться: ' + cross
    if reply_post:
        reply = 'Ответный пост: ' + tick
    else:
        reply = 'Ответный пост: ' + cross
    if notifications_off:
        notif_text = no_bell
    else:
        notif_text = bell
    if new_markup:
        trashbin = emojize(':wastebasket:')
    else:
        trashbin = ''
    if not is_media_group:
        buttons = [
            [types.InlineKeyboardButton(text="Изменить сообщение", callback_data="prf_edit")],
           # [types.InlineKeyboardButton(text="Изменить фото", callback_data="prf_edit_photo")],
           # [types.InlineKeyboardButton(text="Гиперссылки", callback_data="prf_link"),
             [types.InlineKeyboardButton(text=trashbin+"URL-кнопки", callback_data="prf_buttons")],
            #[types.InlineKeyboardButton(text="Спойлер", callback_data="prf_spoiler"),
             [types.InlineKeyboardButton(text="Скрытое продолжение", callback_data="prf_continuation")],
            [types.InlineKeyboardButton(text='Уведомления: '+notif_text, callback_data="prf_notifications")],
            [types.InlineKeyboardButton(text=comms, callback_data="prf_disablecomms")],
            [types.InlineKeyboardButton(text="Репост: " + cross, callback_data="prf_reposton"),
             types.InlineKeyboardButton(text=pin_text, callback_data="prf_pin"),
             types.InlineKeyboardButton(text=share_text, callback_data="prf_share")],
            [types.InlineKeyboardButton(text=reply, callback_data="prf_reply")],
            [types.InlineKeyboardButton(text="Закончить редактирование", callback_data="prf_end")]
        ]
    else:
        buttons = [
            [types.InlineKeyboardButton(text="Изменить сообщение", callback_data="prf_edit"),
             types.InlineKeyboardButton(text="Изменить подпись", callback_data="prf_editcaption")],
            # [types.InlineKeyboardButton(text="Гиперссылки", callback_data="prf_link"),
            #  types.InlineKeyboardButton(text="Спойлер", callback_data="prf_spoiler")],
            # types.InlineKeyboardButton(text="URL-кнопки", callback_data="prf_buttons")],
            # [types.InlineKeyboardButton(text="Скрытое продолжение", callback_data="prf_continuation")],
            [types.InlineKeyboardButton(text='Уведомления: ' + notif_text, callback_data="prf_notifications")],
            [types.InlineKeyboardButton(text=comms, callback_data="prf_disablecomms")],
            #  [types.InlineKeyboardButton(text="Репост: " + cross, callback_data="prf_reposton"),
            [types.InlineKeyboardButton(text=pin_text, callback_data="prf_pin")],
            #  types.InlineKeyboardButton(text=share_text, callback_data="prf_share"+str(not share))],
            [types.InlineKeyboardButton(text=reply, callback_data="prf_reply")],
            [types.InlineKeyboardButton(text="Закончить редактирование", callback_data="prf_end")]
        ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_keyboard_preferences_repost(pin, notifications_off):
    if pin:
        pin_text = 'Закрепить: вкл'
    else:
        pin_text = 'Закрепить: откл'
    if notifications_off:
        notif_text = no_bell
    else:
        notif_text = bell
    buttons = [
        [types.InlineKeyboardButton(text=notif_text, callback_data="prf_notifications")],
        [types.InlineKeyboardButton(text="Репост: вкл", callback_data="prf_repost_off"),
         types.InlineKeyboardButton(text=pin_text, callback_data="prf_pin")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
#
# def get_keyboard_preferences_media_group(restrict_comms, pin, share, reply_post, notifications_off):
#
#     if restrict_comms:
#         comms = 'Включить комментарии'
#     else:
#         comms = 'Отключить комментарии'
#     if pin:
#         pin_text = 'Закрепить: ' + tick
#     else:
#         pin_text = 'Закрепить: ' + cross
#     if share:
#         share_text = 'Поделиться: ' + tick
#     else:
#         share_text = 'Поделиться: ' + cross
#     if reply_post:
#         reply = 'Ответный пост: ' + tick
#     else:
#         reply = 'Ответный пост: ' + cross
#     if notifications_off:
#         notif_text = no_bell
#     else:
#         notif_text = bell
#
#     keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
#     return keyboard
