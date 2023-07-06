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
from Bot import bot
from inline_keyboards.message_preferences import get_keyboard_preferences, get_keyboard_preferences_repost


async def start_forwarding(message: types.Message, state: FSMContext):
    list_of_channels = await create_list_of_channels(message['from']['id'])
    if not list_of_channels:
        await message.answer('Вы не добавили ни одного канала. Сначала добавьте канал при помощи /add_channel')
        await state.finish()
        return
    #   async with state.proxy() as data:
    #       data['sender_id'] = message.from_user.id
    await message.answer('Скиньте сообщение для пересылки')
    #await message.answer(sex)
    await state.set_state(ForwardingMessages.WaitingForMessage.state)


async def forward_not_media_group(message: types.Message, state: FSMContext):
    msg_id = message.message_id
    async with state.proxy() as data:
        data['hidden_continuation_all'] = []
        data['hidden_continuation_text'] = []
        data['hidden_continuation_subs'] = []
        data['restrict_comms'] = False
        data['pin'] = False
        data['share'] = False
        data['reply_post'] = False
        data['repost'] = False
        data['media_group'] = False
        data['message_id'] = msg_id
        data['reply_markup'] = None
        data['message'] = message
        data['link'] = None
        if message.reply_markup:
            data['reply_markup'] = message.reply_markup.inline_keyboard
        ##     if not data['media_group']:

        #            await bot.copy_message(data['message_id'], chat_id=message.from_user.id)
       # await message.answer(message)
        data['menu_msg'] = await message.answer("Выберите нужные настройки", reply_markup=get_keyboard_preferences(
            data['restrict_comms'], data['pin'], data['share'], data['reply_post']))
    #await state.set_state(ForwardingMessages.CustomizingMessage.state)
    #await message.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")


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
    await state.set_state(ForwardingMessages.CustomizingMessage.state)
   # await message.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")


#async def customize_the_message(message: types.Message, state: FSMContext):



async def proceeding_customization(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    async with state.proxy() as data:
    #   await bot.send_message(text=callback, chat_id=1186221701)
        data['action'] = action
        if action == 'edit':
            await bot.send_message(text='Пришлите новое сообщение', chat_id=callback.from_user.id)
            #await callback.answer('Введите текст')
       # elif action == 'edit_photo':
       #     await bot.send_message(text='Отправьте фото', chat_id=callback.from_user.id)
       #     #await callback.answer('Отправьте фото')
        elif action == 'reactions':
            await bot.send_message(text="Разраб долбаеб и это ещё не сделал, сорян", chat_id=callback.from_user.id)
            #await callback.answer("Разраб долбаеб и это ещё не сделал, сорян")
        elif action == 'continuation':
            #await bot.send_message(text=data['menu_msg'].chat.id, chat_id=callback.from_user.id)
            await bot.send_message(text='Отправьте название кнопки', chat_id=callback.from_user.id)
            #await callback.answer('Отправьте название кнопки')
        elif action == 'link':
            if not data['message'].text and not data['message'].caption:
                await callback.answer("Нельзя добавить гиперссылку к сообщению без текста")
                return
            #await bot.send_message(text=data['menu_msg'].chat.id, chat_id=callback.from_user.id)
            await bot.send_message(text='Отправьте ссылку', chat_id=callback.from_user.id)
        elif action == 'end':
            await bot.send_message(text="Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm", chat_id=callback.from_user.id)
            #await callback.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")
            await state.set_state(ForwardingMessages.WaitingForTimeToSchedule.state)
            return
            #bot.answer_callback_query(callback_query_id=callback.id, text="Неверно, Верный ответ...", show_alert=True)
        await bot.delete_message(message_id=data['menu_msg'].message_id, chat_id=data['menu_msg'].chat.id)
        await state.set_state(ForwardingMessages.ProceedingCustomization.state)


async def customization(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data['action'] == 'edit':
            data['message_id'] = message.message_id
        elif data['action'] == 'edit_photo':
            data['message']['photo'] = message.photo
        elif data['action'] == 'reactions':
            pass
            #ToDo че за реакшнс блять?Надо с ними разобраться
        elif data['action'] == 'continuation':
            data['hidden_continuation_text'].append(message.text)
            await message.answer('Введите текст только для подписчиков')
            await state.set_state(ForwardingMessages.HiddenContinuationForAll.state)

        elif data['action'] == 'link':

            data['link'] = message.text
            await message.answer('Введите два номера символов в сообщении через пробел('
                                 'первый символ - начало гиперссылки, второй символ - конец)')
            await state.set_state(ForwardingMessages.HyperLink.state)


async def hyperlink(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data['message'].text:
            msg_text = data['message'].text
            data['type_of_string'] = 'text'
        else:
            msg_text = data['message'].caption
            data['type_of_string'] = 'caption'

        try:
            if int(message.text.split(' ')[0]) > len(msg_text) or int(message.text.split(' ')[0]) < 0:
                await message.answer('Символа с таким номером не существует в сообщении. Попробуйте ещё раз')
                await message.answer(data['message'].text)
                await message.answer(len(data['message'].text))
                await message.answer(message.text.split(' '))
                await state.set_state(ForwardingMessages.HyperLink.state)
                return
            elif int(message.text.split(' ')[1]) > len(msg_text) or int(message.text.split(' ')[1]) < 0:
                await message.answer('Символа с таким номером не существует в сообщении. Попробуйте ещё раз')
                await state.set_state(ForwardingMessages.HyperLink.state)
                return
            elif int(message.text.split(' ')[1]) < int(message.text.split(' ')[0]):
                await message.answer('Номер первого символа не может быть больше номера второго. Попробуйте ещё раз')
                await state.set_state(ForwardingMessages.HyperLink.state)
                return
        except ValueError:
            await message.answer('Неверно указана последовательность. Попробуйте ещё раз')
            await state.set_state(ForwardingMessages.HyperLink.state)
            return
        data['link_start_and_finish'] = str(int(message.text.split(' ')[0])) + ' ' + str(int(message.text.split(' ')[1]) + 1)
        #data['link_start_and_finish'] = message.text
        await message.answer('Гиперссылка успешно добавлена')
        # await bot.send_photo(photo=data['message'].photo, caption=data['message'].text, parse_mode='HTML',
        #                      chat_id=data['message'].ч.id)
        #wait message.answer(text=data['message'].text, parse_mode='HTML')
        data['menu_msg'] = await message.answer("Выберите нужные настройки", reply_markup=get_keyboard_preferences(
            data['restrict_comms'], data['pin'], data['share'], data['reply_post']))


async def continuation_for_all(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['hidden_continuation_subs'].append(message.text)
        await message.answer('Введите текст только для тех, кто не подписан')
        await state.set_state(ForwardingMessages.HiddenContinuationForSubs.state)


async def continuation_for_subs(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['hidden_continuation_all'].append(message.text)
        # buttons = [
        #     [types.InlineKeyboardButton(text="Назад", callback_data="hidden_back")],
        #     [types.InlineKeyboardButton(text="Ещё одно", callback_data="hidden_proceed")]
        # ]
        # keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        # data['menu_msg']

        # bot.delete_message(data['menu_msg'].message_id, chat_id=data['menu_msg'].from_user.id)
        data['menu_msg'] = await message.answer('Скрытое продолжение успешно добавлено.', reply_markup=get_keyboard_preferences(
            data['restrict_comms'], data['pin'], data['share'], data['reply_post']))


async def continuation_choice(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    if action == 'back':
        await state.set_state(ForwardingMessages.ProceedingCustomization.state)
    else:
       # await state.set_state(ForwardingMessages.ProceedingCustomization.state)
        await callback.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")
        await state.set_state(ForwardingMessages.WaitingForTimeToSchedule.state)



async def forward_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await bot.delete_message(message_id=data['menu_msg'].message_id, chat_id=data['menu_msg'].chat.id)
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
                if data['hidden_continuation_text']:
                    # data['hidden_continuation_all'] = []
                    # data['hidden_continuation_text'] = []
                    # data['hidden_continuation_subs'] = []
                    for i in range(len(data['hidden_continuation_text'])):
                        mrkup = Keyboard(markup_id=msg_id, content_text=data['hidden_continuation_text'][i],
                                         content_for_all=data['hidden_continuation_all'][i],
                                         content_for_subs=data['hidden_continuation_subs'][i])
                        db_sess.add(mrkup)
                if data['link']:
                    startlink = int(data['link_start_and_finish'].split(' ')[0]) - 1
                    finishlink = int(data['link_start_and_finish'].split(' ')[1]) - 1
                    if data['type_of_string'] == 'text':
                        startmessage = data['message'].text[:startlink]
                        finishmessage = data['message'].text[finishlink:]
                        middlemessage = data['message'].text[startlink:finishlink]
                    else:
                        startmessage = data['message'].caption[:startlink]
                        finishmessage = data['message'].caption[finishlink:]
                        middlemessage = data['message'].caption[startlink:finishlink]
                    mlink = data['link']
                    link = f'<a href="{mlink}">{middlemessage}</a>'
                    mrkup = Keyboard(markup_id=msg_id,
                                     content_url_text=startmessage+link+finishmessage,
                                     type_of_string=data['type_of_string'])
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
    dp.register_message_handler(hyperlink, state=ForwardingMessages.HyperLink,
                                content_types=types.ContentType.TEXT)
    dp.register_callback_query_handler(proceeding_customization, lambda c: c.data and c.data.startswith('prf'), state='*')

    dp.register_message_handler(customization, state=ForwardingMessages.ProceedingCustomization,
                                content_types=types.ContentType.ANY)
    dp.register_message_handler(continuation_for_all, state=ForwardingMessages.HiddenContinuationForAll,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(continuation_for_subs, state=ForwardingMessages.HiddenContinuationForSubs,
                                content_types=types.ContentType.TEXT)
    dp.register_callback_query_handler(continuation_choice, lambda c: c.data and c.data.startswith('hidden'),state='*')


    dp.register_message_handler(forward_time, state=ForwardingMessages.WaitingForTimeToSchedule,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(forward_channel, state=ForwardingMessages.WaitingForChannelsToBeChosen,
                                content_types=types.ContentType.TEXT)
