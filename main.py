import logging
import sqlite3
import datetime
from aiogram import Bot, Dispatcher, executor, types
from data import db_session
from data.user_class import User
from data.message_class import Message
from data.channel_class import Channel
import config
from aiogram.dispatcher import FSMContext
from fsm import ForwardingMessages, AddChannels
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aioschedule

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot, storage=storage)

db_session.global_init("data.db3")





def create_list_of_channels(user_id):
    db_sess = db_session.create_session()
    db_id = db_sess.query(User).filter(User.tg_id == user_id).first().id
    list_of_channels = db_sess.query(Channel).filter(Channel.user_id == db_id).all()
    db_sess.close()
    result = []
    for i in list_of_channels:
        username = i.ch_username
        if username:
            result.append(f'\n@{username}')
    return result


# registration
@dp.message_handler(commands='start')
async def start(message: types.Message):
    db_sess = db_session.create_session()
    id = int(message['from']['id'])
    if db_sess.query(User).filter((User.tg_id == id)).first():
        await message.answer("Вы уже зарегистрированы")
    else:
        user = User(tg_id=id, username=message['from']['username'])
        db_sess.add(user)
        db_sess.commit()
        db_sess.close()
        await message.answer(f"Добро пожаловать, {message['from']['first_name']}")


# adding a new channel
@dp.message_handler(commands='add_channel')
async def add_channel(message: types.Message, state: FSMContext):
    await message.answer('''Пожалуйста перешлите сообщение из вашего канала
или напишите /cancel для отмены''')
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
            data['username'] = message['forward_from_chat']['username']
        await message.answer(f'''Вы добавили канал: @{message['forward_from_chat']['username']}. Для завершения сделайте 
<code>@ChannelMsgDelayer_bot</code> администратором вашего канала
Напишите /check когда сделаете бота администратором
или /cancel для отмены''', parse_mode='HTML')
        await AddChannels.next()
        db_sess.close()


# adding a new channel
@dp.message_handler(state=AddChannels.WaitingForAdministration.state, commands='check')
async def administration_check(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            member = await bot.get_chat_member(data['tg_id'], int(config.TOKEN.split(':')[0]))
            if member['status'] == "administrator":
                db_sess = db_session.create_session()
                user = Channel(user_id=data['user_id'], tg_id=data['tg_id'], ch_username=data['username'])
                db_sess.add(user)
                db_sess.commit()
                db_sess.close()
                await message.answer('Успех')
                await state.finish()
            else:
                await message.answer('Вы ещё не сделали бота администратором, пожалуйста повторите попытку')

        except Exception as e:
            if str(e) == "Member list is inaccessible":
                await message.answer(f'Что-то пошло не так, ошибка: "{e}"')
                await state.finish()


# list of channels
@dp.message_handler(commands=['channels_list', 'list_of_channels'])
async def get_list_of_channels(message: types.Message):
    list_of_channels = create_list_of_channels(int(message['from']['id']))
    if len(list_of_channels) == 0:
        await message.answer('Вы ещё не добавили ни один канал')
    else:
        result = 'Ваши добавленные каналы:'
        for i in list_of_channels:
            username = i.ch_username
            if username:
                result += f'\n@{username}'
        await message.answer(result)


@dp.message_handler(commands='forward')
async def start_forwarding(message: types.Message, state: FSMContext):
    await message.answer('Скиньте сообщение для пересылки')
    await state.set_state(ForwardingMessages.WaitingForMessage.state)


@dp.message_handler(state=ForwardingMessages.WaitingForMessage, content_types=types.ContentType.ANY)
async def forward(message: types.Message, state: FSMContext):
    # try:
    #     await message.send_copy(chat_id=-1001945938118)
    # except TypeError:
    #     await message.reply(text='Данный тип апдейтов не поддерживается '
    #                              'методом send_copy')
    msg_id = message.message_id
    async with state.proxy() as data:
        data['message_id'] = msg_id
    await ForwardingMessages.next()

    await message.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm:ss")


@dp.message_handler(state=ForwardingMessages.WaitingForTimeToSchedule, content_types=types.ContentType.TEXT)
async def forward_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['pubdate'] = message.text
    await message.answer('Напишите айди канала, в который нужно прислать сообщение')
    await ForwardingMessages.next()

#TODO buttons instead of typing channel's ID
@dp.message_handler(state=ForwardingMessages.WaitingForChannelsToBeChosen, content_types=types.ContentType.TEXT)
async def forward_channel(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['channel_id'] = message.text
        await message.answer(data)
        await message.answer(message.from_user.id)
        dt = datetime.datetime.strptime(data['pubdate'], '%Y-%m-%d-%H:%M:%S')
        await message.answer(dt)
        db_sess = db_session.create_session()
        Msg = Message(tg_id=data['message_id'], sender_id=message.from_user.id, channel_id=data['channel_id'],date=dt)
        db_sess.add(Msg)
        db_sess.commit()
        db_sess.close()
    await state.finish()
    await message.answer('i sex uyr mom')




async def post_message():
    pass

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)

