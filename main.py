import logging
from aiogram import Bot, Dispatcher, executor, types
from data import db_session
from data.user_class import User

import config


logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)

db_session.global_init("data.db3")


@dp.message_handler(commands='start')
async def start(message: types.Message):
    db_sess = db_session.create_session()
    id = int(message['from']['id'])
    if db_sess.query(User).filter(User.tg_id == id).first():
        await message.answer("Вы уже зарегистрированы")
    else:
        user = User(tg_id=id)
        db_sess.add(user)
        db_sess.commit()
        await message.answer(f"Добро пожаловать, {message['from']['first_name']}")


@dp.message_handler(content_types=[types.ContentType.ANY])
async def echo(message: types.Message):

    if message.text is not None:
        await bot.send_message(-1001945938118, message.text)
    elif message.photo is not None:
        await bot.send_photo(chat_id=-1001945938118, photo=message.photo[-1].file_id,
                             caption=message.caption)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
