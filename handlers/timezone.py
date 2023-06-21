from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from data import db_session
from data.user_class import User
from inline_keyboards.timezone_change import get_keyboard_world, get_keyboard_europe, get_keyboard_asia


async def timezone_change_starting(message: types.Message):
    db_sess = db_session.create_session()
    timezone = db_sess.query(User).filter(User.tg_id == message.from_user.id).first().timezone
    db_sess.close()
    await message.answer('Ваш текущий часовой пояс: ' + str(timezone))
    await message.answer(text='Выберите часть света, в которой вы проживаете, из выпадающего списка',
                         reply_markup=get_keyboard_world())


async def timezone_change_proceeding(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    if action == "Europe":
        await callback.message.answer(text='Выберите свой часовой пояс', reply_markup=get_keyboard_europe())
    elif action == "Asia":
        await callback.message.answer(text='Выберите свой часовой пояс', reply_markup=get_keyboard_asia())


async def timezone_change(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    db_sess = db_session.create_session()
    db_sess.query(User).filter(User.tg_id == callback.from_user.id).update({'timezone': int(action)})
    db_sess.commit()
    db_sess.close()
    await callback.message.answer('Часовой пояс успешно изменён на UTC' + action)


def setup(dp: Dispatcher):
    dp.register_message_handler(timezone_change_starting, commands="timezone")
    dp.register_callback_query_handler(timezone_change_proceeding, lambda c: c.data and c.data.startswith('tmz'))
    dp.register_callback_query_handler(timezone_change, lambda c: c.data and c.data.startswith('UTC'))
