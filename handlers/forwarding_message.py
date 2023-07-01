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
        if message.reply_markup:
            data['reply_markup'] = message.reply_markup.inline_keyboard
        ##     if not data['media_group']:

        #            await bot.copy_message(data['message_id'], chat_id=message.from_user.id)
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
        data['action'] = action
        if action == 'edit':
            await callback.answer('Введите текст')
        elif action == 'edit_photo':
            await callback.answer('Отправьте фото')
        elif action == 'reactions':
            await callback.answer("Разраб долбаеб и это ещё не сделал, сорян")
        elif action == 'continuation':
            await callback.answer('Отправьте название кнопки')
        elif action == 'end':
            await callback.answer("Напишите дату отправки сообщения в формате yyyy-MM-dd-HH:mm")
            await state.set_state(ForwardingMessages.WaitingForTimeToSchedule.state)
            return
            #bot.answer_callback_query(callback_query_id=callback.id, text="Неверно, Верный ответ...", show_alert=True)
        await state.set_state(ForwardingMessages.ProceedingCustomization.state)


async def customization(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data['action'] == 'edit':
            data['message']['text'] = message.text
        elif data['action'] == 'edit_photo':
            data['message']['photo'] = message.photo
        elif data['action'] == 'reactions':
            pass
            #ToDo че за реакшнс блять?Надо с ними разобраться
        elif data['action'] == 'continuation':
            data['hidden_continuation_text'].append(message.text)
            await message.answer('Введите текст только для подписчиков')
            await state.set_state(ForwardingMessages.HiddenContinuationForAll.state)


        elif data['action'] == 'buttons':
            pass


async def continuation_for_all(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['hidden_continuation_subs'].append(message.text)
        await message.answer('Введите текст только для тех, кто не подписан')
        await state.set_state(ForwardingMessages.HiddenContinuationForSubs.state)


async def continuation_for_subs(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['hidden_continuation_all'].append(message.text)
        buttons = [
            [types.InlineKeyboardButton(text="Назад", callback_data="hidden_back")],
            [types.InlineKeyboardButton(text="Ещё одно", callback_data="hidden_proceed")]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer('Скрытое продолжение успешно добавлено.'
                             ' Добавим ещё одно или вернёмся к остальным настройкам?', reply_markup=keyboard)


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
#    dp.register_message_handler(customize_the_message, state=ForwardingMessages.CustomizingMessage,
#                                content_types=types.ContentType.TEXT)
    dp.register_callback_query_handler(proceeding_customization, lambda c: c.data and c.data.startswith('prf'), state='*')

    dp.register_message_handler(customization, state=ForwardingMessages.ProceedingCustomization,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(continuation_for_all, state=ForwardingMessages.HiddenContinuationForAll,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(continuation_for_subs, state=ForwardingMessages.HiddenContinuationForSubs,
                                content_types=types.ContentType.TEXT)
    dp.register_callback_query_handler(continuation_choice, lambda c: c.data and c.data.startswith('hidden'),state='*')


    dp.register_message_handler(forward_time, state=ForwardingMessages.WaitingForTimeToSchedule,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(forward_channel, state=ForwardingMessages.WaitingForChannelsToBeChosen,
                                content_types=types.ContentType.TEXT)
