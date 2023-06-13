import logging
from aiogram import Bot, Dispatcher, executor, types
from data import db_session
from data.user_class import User
from data.channel_class import Channel
from data.message_class import Message
import config
from aiogram.dispatcher import FSMContext
from fsm import ForwardingMessages, AddChannels#, DealWithPhotos
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import datetime
# import Delayer
# import aioschedule
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import List, Union
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot, storage=storage)
db_session.global_init("data.db3")


async def create_list_of_channels(user_id):
    db_sess = db_session.create_session()
    db_id = db_sess.query(User).filter(User.tg_id == user_id).first().id
    list_of_channels = db_sess.query(Channel).filter(Channel.user_id == db_id).all()
    db_sess.close()
    result = []
    for i in list_of_channels:
        username = i.ch_username
        if username:
            result.append(f'@{username}')
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
    try:
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
    except Exception as e:
        if type(e) == TypeError:
            await message.answer('вы не переслали сообщение, попробуйте ещё раз')


# adding a new channel
@dp.message_handler(state=AddChannels.WaitingForAdministration.state, commands='check')
async def administration_check(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            member = await bot.get_chat_member(data['tg_id'], int(config.TOKEN.split(':')[0]))
            sender = await bot.get_chat_member(data['tg_id'], message.from_user.id)
            if not member["can_post_messages"]:
                await message.answer('Дайте боту возможность писать сообщения, и повторите попытку(/check)')
            elif member['status'] == "administrator" \
                    and sender['status'] == "administrator" or sender['status'] == "creator":
                db_sess = db_session.create_session()
                user = Channel(user_id=data['user_id'], tg_id=data['tg_id'], ch_username=data['username'])
                db_sess.add(user)
                db_sess.commit()
                db_sess.close()
                await message.answer('Успех')
                await state.finish()
            else:
                await message.answer('Вы не являетесь администратором этого канала')
                await state.finish()

        except Exception as e:
            await message.answer(f'Что-то пошло не так, ошибка: "{e}"')
            await state.finish()


# list of channels
@dp.message_handler(commands=['channels_list', 'list_of_channels'])
async def get_list_of_channels(message: types.Message):
    list_of_channels = await create_list_of_channels(int(message['from']['id']))
    if len(list_of_channels) == 0:
        await message.answer('Вы ещё не добавили ни один канал')
    else:
        result = 'Ваши добавленные каналы:\n'
        for i in list_of_channels:
            if i: result += i + '\n'
        await message.answer(result)


@dp.message_handler(commands='forward')
async def start_forwarding(message: types.Message, state: FSMContext):
 #   async with state.proxy() as data:
 #       data['sender_id'] = message.from_user.id
    await message.answer('Скиньте сообщение для пересылки')
    await state.set_state(ForwardingMessages.WaitingForMessage.state)


# @dp.message_handler(is_media_group=False, state=ForwardingMessages.WaitingForMessage, content_types=types.ContentType.ANY)
# async def forward(message: types.Message, state: FSMContext):
#     await message.answer('После альбома напишите подпись к нему. Если подписи нет, то поставьте прочерк "-"')
#     # try:
#     #     await message.send_copy(chat_id=-1001945938118)
#     # except TypeError:
#     #     await message.reply(text='Данный тип апдейтов не поддерживается '
#     #                              'методом send_copy')
#     # return
#     # msg_id = message.message_id
#     async with state.proxy() as data:
#         if message.text == '-':
#             await message.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")
#             return
#         data['message_id'] = message.message_id
#     await message.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")
#     await ForwardingMessages.next()




# async def forward_photos(message, state: FSMContext):
#     await photo_handler(message=message)
#     #async with state.proxy() as data:
#     #    data['photo_id'] = []
#     #    file_info_1 = message.photo[-1].file_id
#     #    data['photo_id'].append(file_info_1)
#      #
#      #   try:
#      #       file_info_1 = message.message_id
#      #       data['message_id'].append(file_info_1)
#      #   except Exception as e:
#      #       print(e)
#     await ForwardingMessages.next()
#
#     await message.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")
#
# #async def handle_with_media_group(message, data):


@dp.message_handler(content_types=types.ContentType.ANY, state=ForwardingMessages.WaitingForMessage)
async def forward(message: types.Message, state: FSMContext):
    if message.content_type == 'photo':
        await state.update_data(photo_0=message.photo[-1].file_id, photo_counter=0)

        await state.set_state(ForwardingMessages.NextPhoto.state)
    else:
        async with state.proxy() as data:
            data['message_id'] = message.message_id
            await message.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")
            await state.set_state(ForwardingMessages.WaitingForTimeToSchedule.state)


@dp.message_handler(content_types=['photo'], state=ForwardingMessages.NextPhoto)
async def next_photo_handler(message: types.Message, state: FSMContext):
    # здесь находимся пока все следуюище сообщения - фото

    async with state.proxy() as data:
        data['photo_counter'] += 1
        photo_counter = data['photo_counter']
        data[f'photo_{photo_counter}'] = message.photo[-1].file_id
    await state.set_state(ForwardingMessages.NextPhoto.state)


@dp.message_handler(content_types=['text'], state=ForwardingMessages.NextPhoto)
async def not_photo_handler(message: types.Message, state: FSMContext):
    # сюда попадаем если следующее сообщение - не фото

    async with state.proxy() as data:
        if message.text == '-':
            await message.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")
           # await message.answer('я насиловал твою мать')
            await state.set_state(ForwardingMessages.WaitingForTimeToSchedule.state)
        else:
            data['message_id'] = message.message_id
           # await message.answer('иди нахуй тупая тварь')
    await message.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")
    await state.set_state(ForwardingMessages.WaitingForTimeToSchedule.state)




@dp.message_handler(state=ForwardingMessages.WaitingForTimeToSchedule, content_types=types.ContentType.TEXT)
async def forward_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data['pubdate'] = datetime.datetime.strptime(message.text, '%Y-%m-%d-%H:%M')
        except:
            await message.answer('Неверно указана дата. Попробуйте еще раз')
            await state.set_state(ForwardingMessages.WaitingForTimeToSchedule.state)
            return
    list_of_channels = await create_list_of_channels(message['from']['id'])
    kb = [
        [types.KeyboardButton(text=i) for i in list_of_channels]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите канал",
        one_time_keyboard=True
    )
    await message.answer('Выберите канал, в который нужно отправить сообщение',
                         reply_markup=keyboard)
    await ForwardingMessages.next()


@dp.message_handler(is_media_group=True, content_types=types.ContentType.ANY)
async def test(message: types.Message):
    await message.answer(message)

@dp.message_handler(state=ForwardingMessages.WaitingForChannelsToBeChosen, content_types=types.ContentType.TEXT)
async def forward_channel(message: types.Message, state: FSMContext):
    types.reply_keyboard.ReplyKeyboardRemove(True)
    async with state.proxy() as data:
        db_sess = db_session.create_session()
        sender_id = db_sess.query(User).filter(User.tg_id == int(message.from_user.id)).first().id
        channel_id = db_sess.query(Channel).filter('@' + Channel.ch_username == message.text,
                                                   sender_id == Channel.user_id).first()

        if channel_id:
            try:
                x = data['photo_counter']
                for i in range(x+1):
                    msg = Message(tg_id=data[f'photo_{i}'], date=data['pubdate'],
                                  sender_id=sender_id, channel_id=channel_id.id, is_part_mediagroup=True)
                    db_sess.add(msg)
                    db_sess.commit()
                try:
                    x = data['message_id']
                    msg = Message(tg_id=data['message_id'], date=data['pubdate'],
                                  sender_id=sender_id, channel_id=channel_id.id, is_part_mediagroup=True)
                    db_sess.add(msg)
                    db_sess.commit()
                except KeyError:
                    pass
                db_sess.close()
                await message.answer('Сообщение успешно запланировано на ' + str(data['pubdate']),
                                     reply_markup=types.ReplyKeyboardRemove())
            except KeyError:
                msg = Message(tg_id=data['message_id'], date=data['pubdate'],
                              sender_id=sender_id, channel_id=channel_id.id, is_part_mediagroup=False)
                db_sess.add(msg)
                db_sess.commit()
                db_sess.close()
                await message.answer('Сообщение успешно запланировано на ' + str(data['pubdate']),
                                    reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.answer('Вы не добавили этот канал, пожалуйста, сначала добавьте его при помощи /add_channel',
                                 reply_markup=types.ReplyKeyboardRemove())
    await state.finish()


async def check_and_post(bot: Bot):
    db_sess = db_session.create_session()
    result = db_sess.query(Message).filter(Message.date <= datetime.datetime.now()).all()
    for row in result:
        await post_message(row, db_sess)
    db_sess.close()


# async for message in get_chat_history(chat_id):
#   print(message.text)


async def post_message(row, db_sess):
    channel_id = db_sess.query(Channel).filter(row.channel_id == Channel.id).first().tg_id
    sender_id = db_sess.query(User).filter(row.sender_id == User.id).first().tg_id
    if row.is_part_mediagroup:
        try:
            int(row.tg_id)
            await bot.copy_message(chat_id=channel_id, from_chat_id=sender_id, message_id=row.tg_id)
        except ValueError:
            await bot.send_photo(chat_id=channel_id, photo=row.tg_id)
    else:
        await bot.copy_message(chat_id=channel_id, from_chat_id=sender_id, message_id=row.tg_id)
    db_sess.query(Message).filter(Message.id == row.id).delete()
    db_sess.commit()


scheduler = AsyncIOScheduler()

scheduler.add_job(check_and_post, trigger='interval', seconds=5, args=(bot,))

scheduler.start()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
