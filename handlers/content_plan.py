import datetime
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from Bot import bot
from server_functions.ChannelsList import create_list_of_channels
from data.DbDeleter import delete_message, delete_media_group
from server_functions.MessagePost import post_media_group, post_message
from data import db_session
from data.channel_class import Channel
from data.message_class import Message
from data.user_class import User
from server_functions.fsm import ContentPlan


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
        # TODO добавить изменение медиагрупп
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


async def message_edit(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        db_sess = db_session.create_session()
        db_sess.query(Message).filter(Message.id == int(data['msg_id'])).update({'tg_id': message.message_id})
        db_sess.commit()
        db_sess.close()
    await message.answer('Сообщение обновлено')
    await state.finish()


def setup(dp: Dispatcher):
    dp.register_message_handler(content_plan_channel_choice, commands='content_plan')
    dp.register_message_handler(content_plan, state=ContentPlan.channel_choice)
    dp.register_callback_query_handler(process_callback_choose_message_action,
                                       lambda c: c.data and c.data.startswith('msg-'))
    dp.register_callback_query_handler(process_callback_edit_message, lambda c: c.data and c.data.startswith('e-'))
    dp.register_message_handler(message_date_edit, state=ContentPlan.date_edit)
    dp.register_message_handler(message_edit, state=ContentPlan.msg_edit)
