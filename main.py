import logging
from aiogram import Bot, Dispatcher, executor, types
from data import db_session
from data.user_class import User
from data.channel_class import Channel
from data.message_class import Message
import config
from aiogram.dispatcher import FSMContext
from fsm import *
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import datetime
# import Delayer
# import aioschedule
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import List, Union
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
import ast

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


# content plan
@dp.message_handler(commands='content_plan')
async def content_plan_channel_choice(message: types.Message, state: FSMContext):
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
    await message.answer('Выберите канал', reply_markup=keyboard)
    await state.set_state(ContentPlan.channel_choice.state)


# content plan
@dp.message_handler(state=ContentPlan.channel_choice)
async def content_plan(message: types.Message, state: FSMContext):
    types.reply_keyboard.ReplyKeyboardRemove(True)
    db_sess = db_session.create_session()
    channel_id = db_sess.query(Channel).filter(message.text == '@' + Channel.ch_username).first().id
    messages = db_sess.query(Message).filter(Message.channel_id == channel_id).all()
    if len(messages) == 0:
        await message.reply('Для этого канала нет запланированных сообщений')
        await state.finish()
        return
    for i in sorted(messages, key=lambda x: x.date):
        sender = db_sess.query(User).filter(i.sender_id == User.id).first()
        if i.mediagroup_id:
            print('asds')
        # TODO разобраться с медиа группами
        else:
            inline_keyboard = types.InlineKeyboardMarkup()
            inline_keyboard.add(types.InlineKeyboardButton('Изменить сообщение', callback_data='msg-e-' + str(i.id)))
            inline_keyboard.add(types.InlineKeyboardButton('Удалить сообщение', callback_data='msg-d-' + str(i.id)))
            inline_keyboard.add(types.InlineKeyboardButton('Опубликовать сообщение сейчас',
                                                           callback_data='msg-n-' + str(i.id)))
            await bot.copy_message(chat_id=message.chat.id, from_chat_id=sender.tg_id, message_id=i.tg_id,
                                   reply_markup=inline_keyboard)
        await message.answer(f'Сообщение запланировано пользователем: @{sender.username} на время {i.date}')
    await state.finish()
    db_sess.close()


# delete messages in content plan
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('msg-'))
async def process_callback_choose_message_action(callback_query: types.CallbackQuery):
    code = callback_query.data.split('-')
    if code[1] == 'e':
        inline_keyboard = types.InlineKeyboardMarkup()
        inline_keyboard.add(types.InlineKeyboardButton('Изменить дату отправки', callback_data='e-d-' + code[2]))
        inline_keyboard.add(types.InlineKeyboardButton('Изменить сообщение', callback_data='e-e-' + code[2]))
        await bot.send_message(callback_query.from_user.id, 'Что вы хотите изменить?',
                               reply_markup=inline_keyboard)
    elif code[1] == 'd':
        db_sess = db_session.create_session()
        db_sess.query(Message).filter(Message.id == int(code[2])).delete()
        db_sess.commit()
        db_sess.close()
        await bot.send_message(callback_query.from_user.id, '👌')
        await bot.send_message(callback_query.from_user.id, '/content_plan обновлен')
    elif code[1] == 'n':
        db_sess = db_session.create_session()
        await post_message(db_sess.query(Message).filter(Message.id == int(code[2])).first(), db_sess)
        db_sess.query(Message).filter(Message.id == int(code[2])).delete()
        db_sess.commit()
        db_sess.close()


# edit messages in content plan
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('e-'))
async def process_callback_edit_message(callback_query: types.CallbackQuery, state: FSMContext):
    code = callback_query.data.split('-')
    async with state.proxy() as data:
        data['msg_id'] = code[2]
    if code[1] == 'e':
        await bot.send_message(callback_query.from_user.id, 'Отправьте измененное сообщение')
        await state.set_state(ContentPlan.msg_edit)
    elif code[1] == 'd':
        await bot.send_message(callback_query.from_user.id,
                               'Напишите новую дату отправки сообщения в формате yyyy-MM-dd-HH:mm')
        await state.set_state(ContentPlan.date_edit)


@dp.message_handler(state=ContentPlan.date_edit)
async def message_date_edit(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        db_sess = db_session.create_session()
        try:
            date = datetime.datetime.strptime(message.text, '%Y-%m-%d-%H:%M')
        except:
            await message.answer('Неверно указана дата. Попробуйте еще раз')
            await state.set_state(ContentPlan.date_edit)
            return
        db_sess.query(Message).filter(Message.id == int(data['msg_id'])).update({'date': date})
        db_sess.commit()
        db_sess.close()
    await message.answer('Новая дата отправки сообщения сохранена')
    await state.finish()


@dp.message_handler(state=ContentPlan.msg_edit)
async def message_edit(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        db_sess = db_session.create_session()
        db_sess.query(Message).filter(Message.id == int(data['msg_id'])).update({'tg_id': message.message_id})
        db_sess.commit()
        db_sess.close()
    await message.answer('Сообщение обновлено')
    await state.finish()


@dp.message_handler(commands='forward')
async def start_forwarding(message: types.Message, state: FSMContext):
    #   async with state.proxy() as data:
    #       data['sender_id'] = message.from_user.id
    await message.answer('Скиньте сообщение для пересылки')
    await state.set_state(ForwardingMessages.WaitingForMessage.state)


@dp.message_handler(content_types=types.ContentType.ANY, state=ForwardingMessages.WaitingForMessage)
async def forward(message: types.Message, state: FSMContext):
    if message.content_type == 'photo':
        await state.update_data(file_0=message.photo[-1].file_id, file_counter=0,
                                mediagroup_id=message.photo[-1].file_id,
                                type_media='photo')
        await state.set_state(ForwardingMessages.NextFile.state)

    elif message.content_type == 'document':
        await state.update_data(file_0=message.document.file_id, file_counter=0, mediagroup_id=message.document.file_id,
                                type_media='document')
        await state.set_state(ForwardingMessages.NextFile.state)

    elif message.content_type == 'audio':
        await state.update_data(file_0=message.audio.file_id, file_counter=0, mediagroup_id=message.audio.file_id,
                                type_media='audio')
        await state.set_state(ForwardingMessages.NextFile.state)

    else:
        async with state.proxy() as data:
            data['message_id'] = message.message_id
            await message.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")
            await state.set_state(ForwardingMessages.WaitingForTimeToSchedule.state)


@dp.message_handler(content_types=['photo'], state=ForwardingMessages.NextFile)
async def next_photo_handler(message: types.Message, state: FSMContext):
    # здесь находимся пока все следуюище сообщения - фото

    async with state.proxy() as data:
        # data['mediagroup_id'] = data['photo_0']
        data['file_counter'] += 1
        file_counter = data['file_counter']
        data[f'file_{file_counter}'] = message.photo[-1].file_id
    await state.set_state(ForwardingMessages.NextFile.state)


@dp.message_handler(content_types=['document'], state=ForwardingMessages.NextFile)
async def next_doc_handler(message: types.Message, state: FSMContext):
    # здесь находимся пока все следующе сообщения - документы
    async with state.proxy() as data:
        # data['mediagroup_id'] = data['photo_0']
        data['file_counter'] += 1
        file_counter = data['file_counter']
        data[f'file_{file_counter}'] = message.document.file_id
    await state.set_state(ForwardingMessages.NextFile.state)


@dp.message_handler(content_types=['audio'], state=ForwardingMessages.NextFile)
async def next_audio_handler(message: types.Message, state: FSMContext):
    # здесь находимся пока все следуюище сообщения - аудио

    async with state.proxy() as data:
        # data['mediagroup_id'] = data['photo_0']
        data['file_counter'] += 1
        file_counter = data['file_counter']
        data[f'file_{file_counter}'] = message.audio.file_id
    await state.set_state(ForwardingMessages.NextFile.state)


@dp.message_handler(content_types=['text'], state=ForwardingMessages.NextFile)
async def not_photo_handler(message: types.Message, state: FSMContext):
    # сюда попадаем если следующее сообщение - не фото

    async with state.proxy() as data:
        if message.text == '-':
            # await message.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")
            await message.answer('я насиловал твою мать')
            await state.set_state(ForwardingMessages.WaitingForTimeToSchedule.state)
        else:
            data['message_id'] = message.text
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
    media_group = types.MediaGroup()
    file_id = 'AgACAgIAAxkBAAIJy2SHh7_H4sdWkdxaG-SaN80GUZAyAAKByDEb4w9BSHmsRy0BSZdoAQADAgADcwADLwQ'
    media_group.attach({"media": file_id, "type": 'photo'})
    await bot.send_media_group(media=media_group, chat_id=1186221701)


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
                x = data['file_counter']
                for i in range(x + 1):
                    msg = Message(tg_id=data[f'file_{i}'], date=data['pubdate'],
                                  sender_id=sender_id, channel_id=channel_id.id, mediagroup_id=data['mediagroup_id'],
                                  type_media=data['type_media'])
                    db_sess.add(msg)
                    db_sess.commit()
                try:
                    x = data['message_id']
                    msg = Message(tg_id='$' + str(data['message_id']), date=data['pubdate'],
                                  sender_id=sender_id, channel_id=channel_id.id, mediagroup_id=data['mediagroup_id'],
                                  type_media=data['type_media'])
                    db_sess.add(msg)
                    db_sess.commit()
                except KeyError:
                    pass
                db_sess.close()
                await message.answer('Сообщение успешно запланировано на ' + str(data['pubdate']),
                                     reply_markup=types.ReplyKeyboardRemove())
            except KeyError:
                msg = Message(tg_id=data['message_id'], date=data['pubdate'],
                              sender_id=sender_id, channel_id=channel_id.id, mediagroup_id=None)
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
    result_mediagroup = db_sess.query(Message).filter(Message.date <= datetime.datetime.now(),
                                                      Message.mediagroup_id != None).all()
    result = db_sess.query(Message).filter(Message.date <= datetime.datetime.now(),
                                           Message.mediagroup_id == None).all()
    mediagroups = []
    # await bot.send_message(chat_id=-1001945938118, text=result_mediagroup)
    for row in result_mediagroup:
        # await bot.send_message(chat_id=-1001945938118, text=result_mediagroup)
        if row.mediagroup_id in mediagroups:
            continue
        else:
            mediagroups.append(row.mediagroup_id)
            media_group = types.MediaGroup()
            result_current_mediagroup = db_sess.query(Message).filter(Message.date <= datetime.datetime.now(),
                                                                      Message.mediagroup_id == row.mediagroup_id).all()
            caption = []
            for current_row in result_current_mediagroup:
                await collect_mediagroup(current_row, db_sess, media_group, caption)

            await send_mediagroup(result_current_mediagroup, db_sess, media_group, caption)
            db_sess.query(Message).filter(result_current_mediagroup[0].mediagroup_id == Message.mediagroup_id).delete()
            db_sess.commit()
    # if result_mediagroup:
    #    await send_mediagroup(result_mediagroup, db_sess, media_group)
    for row in result:
        await post_message(row, db_sess)
    db_sess.close()


async def post_message(row, db_sess):
    channel_id = db_sess.query(Channel).filter(row.channel_id == Channel.id).first().tg_id
    sender_id = db_sess.query(User).filter(row.sender_id == User.id).first().tg_id

    await bot.copy_message(chat_id=channel_id, from_chat_id=sender_id, message_id=row.tg_id)
    db_sess.query(Message).filter(Message.id == row.id).delete()
    db_sess.commit()


async def collect_mediagroup(row, db_sess, media_group, caption):
    if '$' in row.tg_id:
        caption.append(row.tg_id)
        caption.append(row.type_media)
    else:
        media_group.attach({"media": row.tg_id, "type": row.type_media})
    # db_sess.query(Message).filter(Message.id == row.id).delete()


async def send_mediagroup(result_mediagroup, db_sess, media_group, caption):
    if caption:
        string_media = str(media_group)  # превращаем в str наш экземпляр класса MediaGroup
        media_group = ast.literal_eval(string_media)  # Превращаем str в list
        if caption[1] == 'document' or caption[1] == 'audio':
            media_group[-1]['caption'] = caption[0][1:]
        else:
            media_group[0]['caption'] = caption[0][1:]
        del caption
    channel_id = db_sess.query(Channel).filter(result_mediagroup[0].channel_id == Channel.id).first().tg_id
    await bot.send_media_group(media=media_group, chat_id=channel_id)


scheduler = AsyncIOScheduler()

scheduler.add_job(check_and_post, trigger='interval', seconds=5, args=(bot,))

scheduler.start()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
