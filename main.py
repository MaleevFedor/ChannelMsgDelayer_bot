import logging
from aiogram import Bot, Dispatcher, executor, types
from data import db_session
from data.user_class import User
from data.channel_class import Channel
import config
from aiogram.dispatcher import FSMContext
from fsm import ForwardingMessages, AddChannels
from aiogram.contrib.fsm_storage.memory import MemoryStorage


logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot, storage=storage)

db_session.global_init("data.db3")


# registration
@dp.message_handler(commands='start')
async def start(message: types.Message):
    db_sess = db_session.create_session()
    id = int(message['from']['id'])
    if db_sess.query(User).filter((User.tg_id == id)).first():
        await message.answer("Вы уже зарегистрированы")
    else:
        user = User(tg_id=id)
        db_sess.add(user)
        db_sess.commit()
        await message.answer(f"Добро пожаловать, {message['from']['first_name']}")


# adding a new channel
@dp.message_handler(commands='add_channel')
async def add_channel(message: types.Message, state: FSMContext):
    await message.answer('Пожалуйста перешлите сообщение из вашего канала')
    await state.set_state(AddChannels.WaitingForMessage.state)


# adding a new channel
@dp.message_handler(state=AddChannels.WaitingForMessage.state, content_types=[types.ContentType.ANY])
async def get_message_from_channel(message: types.Message, state: FSMContext):
    db_sess = db_session.create_session()
    channel_id = message['forward_from_chat']['id']
    cur_user_id = db_sess.query(User).filter(User.tg_id == int(message['from']['id'])).first().id
    if db_sess.query(Channel).filter(Channel.tg_id == channel_id,
                                     Channel.user_id == cur_user_id).first():
        await message.reply("Вы уже добавили этот канал, попробуйте ещё раз")
        await state.finish()
    else:
        async with state.proxy() as data:
            data['user_id'] = cur_user_id
            data['tg_id'] = channel_id
        await message.answer(f'''Вы добавили канал: @{message['forward_from_chat']['username']}. Для завершения сделайте 
<code>@ChannelMsgDelayer_bot</code> администратором вашего канала
Напишите /check когда сделаете бота администратором''', parse_mode='HTML')
        await AddChannels.next()
        db_sess.close()


# adding a new channel
@dp.message_handler(state=AddChannels.WaitingForAdministration.state, commands='check')
async def administration_check(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            for i in await bot.get_chat_administrators(data['tg_id']):
                if i["user"]['id'] == int(config.TOKEN.split(':')[0]):
                    break
            else:
                await message.answer('Вы ещё не сделали бота администратором, пожалуйста повторите попытку')
            await message.answer('Успех')
            db_sess = db_session.create_session()
            user = Channel(user_id=data['user_id'], tg_id=data['tg_id'])
            db_sess.add(user)
            db_sess.commit()
            await state.finish()
        except Exception as e:
            if str(e) == "Member list is inaccessible":
                await message.answer('Вы ещё не сделали бота администратором или указали неверный канал,пожалуйста '
                                     f'начните заново, ошибка: "{e}"')
                await state.finish()


# list of channels
@dp.message_handler(commands=['channels_list', 'list_of_channels'])
async def get_list_of_channels(message: types.Message):
    db_sess = db_session.create_session()
    user_id = int(message['from']['id'])
    db_id = db_sess.query(User).filter(User.tg_id == user_id).first().id
    for i in db_sess.query(Channel).filter(Channel.user_id == db_id).all():
        print(i.tg_id)


@dp.message_handler(state=AddChannels.WaitingForAdministration)
async def forward(message: types.Message, state: FSMContext):
    if message.text is not None:
        await bot.send_message(-1001945938118, message.text)
    elif message.photo is not None:
        await bot.send_photo(chat_id=-1001945938118, photo=message.photo[-1].file_id,
                             caption=message.caption)
    await state.finish()


@dp.message_handler(commands='forward')
async def start_forwarding(message: types.Message, state: FSMContext):
    await message.answer('Скиньте сообщение для пересылки')
    await state.set_state(ForwardingMessages.WaitingForMessage.state)


@dp.message_handler(state=ForwardingMessages.WaitingForMessage, content_types=types.ContentType.ANY)
async def forward(message: types.Message, state: FSMContext):
    if message.text is not None:
        await bot.send_message(-1001945938118, message.text)
    elif message.photo is not None:
        await bot.send_photo(chat_id=-1001945938118, photo=message.photo[-1].file_id,
                             caption=message.caption)
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
