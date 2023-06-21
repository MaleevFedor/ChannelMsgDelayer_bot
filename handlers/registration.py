from aiogram import types, Dispatcher
from data import db_session
from data.user_class import User


async def start(message: types.Message):
    db_sess = db_session.create_session()
    id = int(message['from']['id'])
    if db_sess.query(User).filter((User.tg_id == id)).first():
        await message.answer("Вы уже зарегистрированы")
    else:
        user = User(tg_id=id, username=message['from']['username'])
        db_sess.add(user)
        db_sess.commit()
        timezone = db_sess.query(User).filter(User.tg_id == message.from_user.id).first().timezone
        db_sess.close()
        await message.answer(f"Добро пожаловать, {message['from']['first_name']}.\n"
                             f"Автоопределён часовой пояс: UTC {timezone}\n"
                             f"Напишите /help для просмотра списка команд")


def setup(dp: Dispatcher):
    dp.register_message_handler(start, commands="start")
