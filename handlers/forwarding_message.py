import datetime
from typing import List
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from server_functions.ChannelsList import create_list_of_channels
from data import db_session
from data.channel_class import Channel
from data.message_class import Message
from data.reply_markup_class import Keyboard
from data.user_class import User
from server_functions.fsm import ForwardingMessages


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


def setup(dp: Dispatcher):
    dp.register_message_handler(start_forwarding, commands='forward')
    dp.register_message_handler(forward_not_media_group, is_media_group=False, content_types=types.ContentType.ANY,
                                state=ForwardingMessages.WaitingForMessage)
    dp.register_message_handler(forward_media_group, is_media_group=True, content_types=types.ContentType.ANY,
                                state=ForwardingMessages.WaitingForMessage)
    dp.register_message_handler(forward_time, state=ForwardingMessages.WaitingForTimeToSchedule,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(forward_channel, state=ForwardingMessages.WaitingForChannelsToBeChosen,
                                content_types=types.ContentType.TEXT)
