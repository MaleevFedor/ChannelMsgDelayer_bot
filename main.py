import logging
from aiogram import Bot, Dispatcher, executor, types
from DbDeleter import *
from data import db_session
from data.reply_markup_class import Keyboard
from data.user_class import User
from data.channel_class import Channel
from data.message_class import Message
from ChannelsList import create_list_of_channels
import config
from aiogram.dispatcher import FSMContext
from fsm import *
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import datetime
from MessagePost import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from AlbumHandler import AlbumMiddleware
from typing import List, Union
from aiogram.dispatcher.handler import CancelHandler
from timezone_change import *


logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot, storage=storage)
db_session.global_init("data.db3")


# time zone change
@dp.message_handler(commands='timezone')
async def timezone_change_starting(message: types.Message):
    db_sess = db_session.create_session()
    timezone = db_sess.query(User).filter(User.tg_id == message.from_user.id).first().timezone
    db_sess.close()
    await message.answer('Ваш текущий часовой пояс: ' + str(timezone))
    await message.answer(text='Выберите часть света, в которой вы проживаете, из выпадающего списка', reply_markup=get_keyboard_world())


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('tmz'))
async def timezone_change_proceeding(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    if action == "Europe":
        await callback.message.answer(text='Выберите свой часовой пояс', reply_markup=get_keyboard_europe())
    elif action == "Asia":
        await callback.message.answer(text='Выберите свой часовой пояс', reply_markup=get_keyboard_asia())


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('UTC'))
async def timezone_change_proceeding(callback: types.CallbackQuery):
    action = callback.data.split("_")[1]
    db_sess = db_session.create_session()
    db_sess.query(User).filter(User.tg_id == callback.from_user.id).update({'timezone': int(action)})
    db_sess.commit()
    db_sess.close()
    await callback.message.answer('Часовой пояс успешно изменён на UTC'+ action)

#
# @dp.message_handler(state=TimeZoneChange.Proceed_The_Choice.state, content_types=[types.ContentType.ANY])
# async def timezone_change_ending(message: types.Message, state: FSMContext):


# commands cancellation
@dp.message_handler(state='*', commands='cancel')
async def cancel_handler(message: types.Message, state: FSMContext):
    await message.answer('Действие отменено')
    await state.finish()


# commands list
@dp.message_handler(commands='help')
async def commands_list(message: types.Message):
    await message.answer("/add_channel - добавить канал\n/forward - запланировать пересылку сообщения\n"
                         "/content_plan - просмотреть список запланированных сообщений\n"
                         "/cancel - отменить любое действие")


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
        timezone = db_sess.query(User).filter(User.tg_id == message.from_user.id).first().timezone
        db_sess.close()
        await message.answer(f"Добро пожаловать, {message['from']['first_name']}.\n"
                             f"Автоопределён часовой пояс: UTC {timezone}\n"
                             f"Напишите /help для просмотра списка команд")


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
    if not list_of_channels:
        await message.answer('Вы не добавили ни одного канала. Сначала добавьте канал при помощи /add_channel')
        await state.finish()
        return
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
    passed_id = set()
    for i in sorted(messages, key=lambda x: x.date):
        sender = db_sess.query(User).filter(i.sender_id == User.id).first()
        if i.mediagroup_id:
            inline_keyboard = types.InlineKeyboardMarkup()
            inline_keyboard.add(types.InlineKeyboardButton('Изменить сообщение', callback_data='msg-mg-e-' + str(i.id)))
            inline_keyboard.add(types.InlineKeyboardButton('Удалить сообщение', callback_data='msg-mg-d-' + str(i.id)))
            inline_keyboard.add(types.InlineKeyboardButton('Опубликовать сообщение сейчас',
                                                           callback_data='msg-mg-n-' + str(i.id)))
            if i.mediagroup_id not in passed_id:
                await post_media_group(i.mediagroup_id, db_sess, bot, channel_id=message.chat.id)
                passed_id.add(i.mediagroup_id)
                await message.answer(f'Сообщение запланировано пользователем: @{sender.username} на время {i.date}',
                                     reply_markup=inline_keyboard)
        else:
            inline_keyboard = types.InlineKeyboardMarkup()
            inline_keyboard.add(types.InlineKeyboardButton('Изменить сообщение', callback_data='msg-m-e-' + str(i.id)))
            inline_keyboard.add(types.InlineKeyboardButton('Удалить сообщение', callback_data='msg-m-d-' + str(i.id)))
            inline_keyboard.add(types.InlineKeyboardButton('Опубликовать сообщение сейчас',
                                                           callback_data='msg-m-n-' + str(i.id)))
            await post_message(i, db_sess, bot, channel_id=message.chat.id)
            await message.answer(f'Сообщение запланировано пользователем: @{sender.username} на время {i.date}',
                                 reply_markup=inline_keyboard)
    await state.finish()
    db_sess.close()


# delete messages in content plan
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('msg-'))
async def process_callback_choose_message_action(callback_query: types.CallbackQuery):
    code = callback_query.data.split('-')
    db_sess = db_session.create_session()
    if code[2] == 'e':
        inline_keyboard = types.InlineKeyboardMarkup()
        inline_keyboard.add(types.InlineKeyboardButton('Изменить дату отправки', callback_data='e-d-' + code[2] + '-' +
                                                       code[3]))
        if code[1] == 'm':
            inline_keyboard.add(types.InlineKeyboardButton('Изменить сообщение', callback_data='e-e-' + code[2] + '-' +
                                                        code[3]))
        else:
            pass
        #TODO добавить изменение медиагрупп
        await bot.send_message(callback_query.from_user.id, 'Что вы хотите изменить?',
                               reply_markup=inline_keyboard)
    elif code[2] == 'd':
        if code[1] == 'm':
            msg = db_sess.query(Message).filter(Message.id == int(code[3])).first()
            await delete_message(msg.tg_id, db_sess)

        else:
            msg = db_sess.query(Message).filter(Message.id == int(code[3])).first()
            await delete_media_group(msg.mediagroup_id, db_sess)
        await bot.send_message(callback_query.from_user.id, '👌')
        await bot.send_message(callback_query.from_user.id, '/content_plan обновлен')
    elif code[2] == 'n':
        if code[1] == 'm':
            msg = db_sess.query(Message).filter(Message.id == int(code[3])).first()
            await post_message(msg, db_sess, bot)
            await delete_message(msg.tg_id, db_sess)
        else:
            msg = db_sess.query(Message).filter(Message.id == int(code[3])).first()
            await post_media_group(msg.mediagroup_id, db_sess, bot)
            await delete_media_group(msg.mediagroup_id, db_sess)
        await bot.send_message(callback_query.from_user.id, 'Сообщение опубликовано👌')
    db_sess.close()


# edit messages in content plan
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('e-'))
async def process_callback_edit_message(callback_query: types.CallbackQuery, state: FSMContext):
    code = callback_query.data.split('-')
    async with state.proxy() as data:
        data['msg_id'] = code[3]
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
    list_of_channels = await create_list_of_channels(message['from']['id'])
    if not list_of_channels:
        await message.answer('Вы не добавили ни одного канала. Сначала добавьте канал при помощи /add_channel')
        await state.finish()
        return
    #   async with state.proxy() as data:
    #       data['sender_id'] = message.from_user.id
    await message.answer('Скиньте сообщение для пересылки')
    await state.set_state(ForwardingMessages.WaitingForMessage.state)


@dp.message_handler(is_media_group=False, content_types=types.ContentType.ANY,
                    state=ForwardingMessages.WaitingForMessage)
async def forward_not_media_group(message: types.Message, state: FSMContext):
    msg_id = message.message_id
    async with state.proxy() as data:
        data['media_group'] = False
        data['message_id'] = msg_id
        data['reply_markup'] = None
        if message.reply_markup:
            data['reply_markup'] = message.reply_markup.inline_keyboard
    await state.set_state(ForwardingMessages.WaitingForTimeToSchedule.state)
    await message.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")


@dp.message_handler(is_media_group=True, content_types=types.ContentType.ANY,
                    state=ForwardingMessages.WaitingForMessage)
async def forward_media_group(message: types.Message, state: FSMContext, album: List[types.Message]):
    async with state.proxy() as data:
        data['media_group'] = True
        data['caption'] = album[0].caption
        for i, obj in enumerate(album):
            if obj.photo:
                result = [str(obj.photo[-1].file_id), str(obj.content_type)]
            else:
                result = [str(obj[obj.content_type].file_id), str(obj.content_type)]
            data[f'msg_{i}'] = result
        data['file_counter'] = len(album)
    await state.set_state(ForwardingMessages.WaitingForTimeToSchedule.state)
    await message.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")


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


@dp.message_handler(state=ForwardingMessages.WaitingForChannelsToBeChosen, content_types=types.ContentType.TEXT)
async def forward_channel(message: types.Message, state: FSMContext):
    types.reply_keyboard.ReplyKeyboardRemove(True)
    async with state.proxy() as data:
        db_sess = db_session.create_session()
        sender_id = db_sess.query(User).filter(User.tg_id == int(message.from_user.id)).first().id
        channel_id = db_sess.query(Channel).filter('@' + Channel.ch_username == message.text,
                                                   sender_id == Channel.user_id).first()
        timezone = db_sess.query(User).filter(User.tg_id == int(message.from_user.id)).first().timezone
        if channel_id:
            date = data['pubdate'] + datetime.timedelta(hours=timezone) - datetime.timedelta(hours=3)
            if data['media_group']:
                mediagroup_id = data['msg_0'][0]
                msg = Message(tg_id=data['caption'], date=date,
                              sender_id=sender_id, channel_id=channel_id.id, mediagroup_id=mediagroup_id,
                              type_media='caption')
                db_sess.add(msg)
                db_sess.commit()
                for i in range(data['file_counter']):
                    msg = data[f'msg_{i}']
                    msg = Message(tg_id=msg[0], date=date,
                                  sender_id=sender_id, channel_id=channel_id.id, mediagroup_id=mediagroup_id,
                                  type_media=msg[1])
                    db_sess.add(msg)
                    db_sess.commit()
            else:
                msg_id = data['message_id']
                msg = Message(tg_id=msg_id, date=date, sender_id=sender_id,
                              channel_id=channel_id.id, reply_markup=True)
                db_sess.add(msg)
                if data['reply_markup']:
                    for i in data['reply_markup']:
                        i = str(*i)
                        mrkup = Keyboard(markup_id=msg_id, content=i)
                        db_sess.add(mrkup)
                db_sess.commit()
            await message.answer('Сообщение успешно запланировано на ' + str(date))
        else:
            await message.answer('Вы не добавили этот канал, пожалуйста, сначала добавьте его при помощи /add_channel',
                                 reply_markup=types.ReplyKeyboardRemove())

        db_sess.close()
    await state.finish()


async def check_and_post(bot: Bot):
    db_sess = db_session.create_session()
    media_groups_id = set(
        [i.mediagroup_id for i in db_sess.query(Message).filter(Message.date <= datetime.datetime.now(),
                                                                Message.mediagroup_id != None).all()])
    not_media_groups = db_sess.query(Message).filter(Message.date <= datetime.datetime.now(),
                                                     Message.mediagroup_id == None).all()
    for row in media_groups_id:
        await post_media_group(row, db_sess, bot)
        await delete_media_group(row, db_sess)
    for row in not_media_groups:
        await post_message(row, db_sess, bot)
        await delete_message(row.tg_id, db_sess)
    db_sess.close()


scheduler = AsyncIOScheduler()

scheduler.add_job(check_and_post, trigger='interval', seconds=5, args=(bot,))

scheduler.start()

if __name__ == '__main__':
    dp.middleware.setup(AlbumMiddleware())
    executor.start_polling(dp, skip_updates=False)
