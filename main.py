import logging
from aiogram import Dispatcher, executor, types
import server_functions.Scheduler as Scheduler
from data import db_session
from DispatcherSetup import setup_dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from Bot import bot
from data.reply_markup_class import Keyboard
import emoji
logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)

db_session.global_init("data.db3")

buttons = [
        [types.InlineKeyboardButton(text="efg", url='efg.com')]]

keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
# @dp.message_handler(content_types=[types.ContentType.ANY])
# async def echo(message: types.Message):
#     chat_id = -1001945938118
#     message_id = 1000
#     try:
#         msg_id = await bot.copy_message(message_id=message_id, chat_id=1186221701, from_chat_id=chat_id)
#         await bot.delete_message(chat_id=message.from_user.id, message_id=msg_id.message_id)
#         message_exists = True
#     except Exception as e:
#         if str(e) == 'Message to copy not found':
#             message_exists = False
#         else:
#             raise e

    # await message.answer(message_exists)
    # user_channel_status = await bot.get_chat_member(chat_id='@testforbot_makar', user_id=6059543486)
    # await message.answer(user_channel_status['status'])


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('test'))
async def inline_button_answer(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback.id, text=callback.message.chat.id, show_alert=True)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('hidden'))
async def display_hidden_continuation(callback: types.CallbackQuery):
    msg_id = callback.data.split("_")[1]
    button_number = int(callback.data.split("_")[2])
    db_sess = db_session.create_session()
    #msg_on_post_id = db_sess.query(Message).filter(Message.tg_id == msg_id).first().id_on_post
    button = db_sess.query(Keyboard).filter(Keyboard.markup_id == msg_id,
                                            Keyboard.content_text != None).all()
    user_channel_status = await bot.get_chat_member(chat_id=callback.message.chat.id, user_id=callback.from_user.id)
    if user_channel_status["status"] != 'left':
        await bot.answer_callback_query(callback_query_id=callback.id, text=button[button_number].content_for_subs,
                                        show_alert=True)
    else:
        await bot.answer_callback_query(callback_query_id=callback.id, text=button[button_number].content_for_all,
                                        show_alert=True)

    await bot.answer_callback_query(callback_query_id=callback.id, text="Твоя мать проститутка!", show_alert=True)

if __name__ == '__main__':
    setup_dispatcher(dp)
    Scheduler.set_up_scheduler(bot)
    executor.start_polling(dp, skip_updates=False)
