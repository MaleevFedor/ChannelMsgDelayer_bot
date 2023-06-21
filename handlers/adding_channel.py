from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from Bot import bot
import config
from data import db_session
from data.channel_class import Channel
from data.user_class import User
from server_functions.fsm import AddChannels


async def add_channel(message: types.Message, state: FSMContext):
    await message.answer('''Пожалуйста перешлите сообщение из вашего канала
или напишите /cancel для отмены''')
    await state.set_state(AddChannels.WaitingForMessage.state)


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
            await message.answer(f'''Вы добавили канал: @{message['forward_from_chat']['username']}. Для завершения
сделайте  <code>@ChannelMsgDelayer_bot</code> администратором вашего канала
Напишите /check когда сделаете бота администратором
или /cancel для отмены''', parse_mode='HTML')
            await AddChannels.next()
            if message['forward_from_chat']['username'] == 'None':
                data['username'] = None
            db_sess.close()
    except Exception as e:
        if type(e) == TypeError:
            await message.answer('вы не переслали сообщение, попробуйте ещё раз')


async def administration_check(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            member = await bot.get_chat_member(data['tg_id'], int(config.TOKEN.split(':')[0]))
            sender = await bot.get_chat_member(data['tg_id'], message.from_user.id)
            if not member["can_post_messages"]:
                await message.answer('Дайте боту возможность писать сообщения, и повторите попытку(/check)')
            elif member['status'] == "administrator" \
                    and sender['status'] == "administrator" or sender['status'] == "creator":
                if not data['username']:
                    await message.answer('Похоже ваш канал закрытый, напиши как бы вы хотели, чтобы бот называл '
                                         'ваш канал. Это название нужно только для того, чтобы вам было проще найти '
                                         'своего бота в списке')
                    await AddChannels.next()
                else:
                    await message.answer('Успех')
                    db_sess = db_session.create_session()
                    user = Channel(user_id=data['user_id'], tg_id=data['tg_id'], ch_username=data['username'])
                    db_sess.add(user)
                    db_sess.commit()
                    db_sess.close()
                    await state.finish()
            else:
                await message.answer('Вы не являетесь администратором этого канала')
                await state.finish()

        except Exception as e:
            await message.answer(f'Что-то пошло не так, ошибка: "{e}"')
            await state.finish()


async def choose_channel_nickname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        db_sess = db_session.create_session()
        user = Channel(user_id=data['user_id'], tg_id=data['tg_id'], ch_username=message.text)
        db_sess.add(user)
        db_sess.commit()
        db_sess.close()
        await state.finish()
        await message.answer(f'Канал "{message.text}" успешно добавлен')


def setup(dp: Dispatcher):
    dp.register_message_handler(add_channel, commands='add_channel')
    dp.register_message_handler(get_message_from_channel,
                                state=AddChannels.WaitingForMessage.state, content_types=[types.ContentType.ANY])
    dp.register_message_handler(administration_check,
                                state=AddChannels.WaitingForAdministration.state, commands='check')
    dp.register_message_handler(choose_channel_nickname, state=AddChannels.Nickname.state)
